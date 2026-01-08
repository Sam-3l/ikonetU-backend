from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
from .models import Video, VideoView, VideoLike
from apps.accounts.models import User
from apps.reports.models import Report
from apps.notifications.services import NotificationService


def require_admin(view_func):
    """Decorator to check if user is admin"""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response({'message': 'Unauthorized'}, status=status.HTTP_401_UNAUTHORIZED)
        if request.user.role != 'admin':
            return Response({'message': 'Admin access required'}, status=status.HTTP_403_FORBIDDEN)
        return view_func(request, *args, **kwargs)
    return wrapper


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@require_admin
def admin_dashboard_stats_view(request):
    """Get admin dashboard statistics"""
    from datetime import datetime
    
    now = timezone.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)
    
    # Total counts
    total_users = User.objects.count()
    total_founders = User.objects.filter(role='founder').count()
    total_investors = User.objects.filter(role='investor').count()

    total_videos = Video.objects.count()
    active_videos = Video.objects.filter(status='active', is_current=True).count()
    pending_videos = Video.objects.filter(status='processing', is_current=True).count()

    pending_reports = Report.objects.filter(status='pending').count()
    
    today_signups = User.objects.filter(created_at__gte=today_start, created_at__lt=today_end).count()
    today_videos = Video.objects.filter(created_at__gte=today_start, created_at__lt=today_end).count()
        
    # For matches
    try:
        from apps.matches.models import Match
        total_matches = Match.objects.filter(is_active=True).count()
        today_matches = Match.objects.filter(
            created_at__gte=today_start, 
            created_at__lt=today_end,
            is_active=True
        ).count()
    except ImportError:
        total_matches = 0
        today_matches = 0

    return Response({
        'total_users': total_users,
        'total_founders': total_founders,
        'total_investors': total_investors,
        'total_videos': total_videos,
        'active_videos': active_videos,
        'pending_videos': pending_videos,
        'total_matches': total_matches,
        'pending_reports': pending_reports,
        'today_signups': today_signups,
        'today_videos': today_videos,
        'today_matches': today_matches,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@require_admin
def admin_users_view(request):
    """Get all users with their profiles and stats"""
    users = User.objects.all().select_related(
        'founder_profile', 'investor_profile'
    ).order_by('-created_at')
    
    try:
        from apps.matches.models import Match
        has_match_model = True
    except ImportError:
        has_match_model = False
    
    users_data = []
    for user in users:
        # Get user stats based on role
        if user.role == 'founder':
            video_count = Video.objects.filter(founder=user).count()
            view_count = VideoView.objects.filter(video__founder=user).count()
            match_count = Match.objects.filter(founder=user, is_active=True).count() if has_match_model else 0
        elif user.role == 'investor':
            video_count = 0
            view_count = 0
            match_count = Match.objects.filter(investor=user, is_active=True).count() if has_match_model else 0
        else:
            video_count = 0
            view_count = 0
            match_count = 0
        
        user_data = {
            'id': str(user.id),
            'name': user.name,
            'email': user.email,
            'role': user.role,
            'avatar_url': user.avatar_url if user.avatar_url else None,
            'created_at': user.created_at.isoformat(),
            'onboarding_complete': user.onboarding_complete,
            'stats': {
                'video_count': video_count,
                'match_count': match_count,
                'view_count': view_count,
            },
            'founder_profile': None,
            'investor_profile': None,
        }
        
        # Add founder profile if exists
        if user.role == 'founder':
            try:
                profile = user.founder_profile
                user_data['founder_profile'] = {
                    'company_name': profile.company_name or '',
                    'sector': profile.sector or '',
                    'stage': profile.stage or '',
                    'location': profile.location or '',
                    'bio': profile.bio or '',
                }
            except Exception:
                pass
        
        # Add investor profile if exists
        if user.role == 'investor':
            try:
                profile = user.investor_profile
                user_data['investor_profile'] = {
                    'firm_name': profile.firm_name or '',
                    'title': profile.title or '',
                    'sectors': profile.sectors if profile.sectors else [],
                    'stages': profile.stages if profile.stages else [],
                }
            except Exception:
                pass
        
        users_data.append(user_data)
    
    return Response(users_data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@require_admin
def admin_videos_view(request):
    """Get all videos for admin review"""
    status_filter = request.GET.get('status', None)

    videos = Video.objects.select_related('founder').order_by('-created_at')

    if status_filter and status_filter != 'all':
        videos = videos.filter(status=status_filter)

    videos_data = []
    for video in videos:
        # Get founder's company name
        company_name = None
        try:
            if hasattr(video.founder, 'founder_profile'):
                company_name = video.founder.founder_profile.company_name
        except Exception:
            pass
        
        # Count views and likes
        view_count = VideoView.objects.filter(video=video).count()
        like_count = VideoLike.objects.filter(video=video).count()
        
        videos_data.append({
            'id': str(video.id),
            'title': video.title,
            'url': video.url,
            'thumbnail_url': video.thumbnail_url,
            'duration': video.duration,
            'status': video.status,
            'is_current': video.is_current,
            'view_count': view_count,
            'like_count': like_count,
            'created_at': video.created_at.isoformat(),
            'founder': {
                'id': str(video.founder.id),
                'name': video.founder.name,
                'email': video.founder.email,
                'company_name': company_name,
            }
        })

    return Response(videos_data)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
@require_admin
def admin_approve_video_view(request, video_id):
    """Approve a video"""
    try:
        video = Video.objects.get(id=video_id)
        video.status = 'active'
        video.save()
        
        NotificationService.create_video_status_notification(video, 'active')
        
        return Response({
            'message': 'Video approved',
            'video': {'id': str(video.id), 'status': video.status}
        })
    except Video.DoesNotExist:
        return Response({'message': 'Video not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
@require_admin
def admin_reject_video_view(request, video_id):
    """Reject a video"""
    try:
        video = Video.objects.get(id=video_id)
        video.status = 'rejected'
        video.save()

        NotificationService.create_video_status_notification(video, 'rejected')

        return Response({
            'message': 'Video rejected',
            'video': {'id': str(video.id), 'status': video.status}
        })
    except Video.DoesNotExist:
        return Response({'message': 'Video not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
@require_admin
def admin_delete_user_view(request, user_id):
    """Delete a user (soft delete - set inactive)"""
    try:
        user = User.objects.get(id=user_id)
        if user.role == 'admin':
            return Response({'message': 'Cannot delete admin users'}, status=status.HTTP_403_FORBIDDEN)
        user.is_active = False
        user.save()
        return Response({'message': 'User deactivated successfully'})
    except User.DoesNotExist:
        return Response({'message': 'User not found'}, status=status.HTTP_404_NOT_FOUND)