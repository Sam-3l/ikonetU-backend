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
    # Get today's date range using timezone-aware datetime
    from datetime import datetime
    
    # Get current time in UTC
    now = timezone.now()
    
    # Get today's start (midnight) in UTC
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Get tomorrow's start (which is today's end)
    today_end = today_start + timedelta(days=1)
    
    # Total counts
    total_users = User.objects.count()
    total_founders = User.objects.filter(role='founder').count()
    total_investors = User.objects.filter(role='investor').count()

    total_videos = Video.objects.count()
    active_videos = Video.objects.filter(status='active', is_current=True).count()
    pending_videos = Video.objects.filter(status='processing', is_current=True).count()

    pending_reports = Report.objects.filter(status='pending').count()
    
    # Today's counts - with detailed debug info
    today_signups = User.objects.filter(created_at__gte=today_start, created_at__lt=today_end).count()
    today_videos = Video.objects.filter(created_at__gte=today_start, created_at__lt=today_end).count()
        
    # Also get recent records to verify
    recent_users = User.objects.order_by('-created_at')[:5]
    recent_videos = Video.objects.order_by('-created_at')[:5]
        
    # For matches, use the Match model if available
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
        'totalUsers': total_users,
        'totalFounders': total_founders,
        'totalInvestors': total_investors,
        'totalVideos': total_videos,
        'activeVideos': active_videos,
        'pendingVideos': pending_videos,
        'totalMatches': total_matches,
        'pendingReports': pending_reports,
        'todaySignups': today_signups,
        'todayVideos': today_videos,
        'todayMatches': today_matches,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@require_admin
def admin_users_view(request):
    """Get all users with their profiles and stats"""
    users = User.objects.all().select_related(
        'founder_profile', 'investor_profile'
    ).order_by('-created_at')
    
    # Import Match model
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
            if has_match_model:
                match_count = Match.objects.filter(founder=user, is_active=True).count()
            else:
                match_count = 0
        elif user.role == 'investor':
            video_count = 0
            view_count = 0
            if has_match_model:
                match_count = Match.objects.filter(investor=user, is_active=True).count()
            else:
                match_count = 0
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
            }
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
            except:
                user_data['founder_profile'] = None
        
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
            except:
                user_data['investor_profile'] = None
        
        users_data.append(user_data)
    
    return Response(users_data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@require_admin
def admin_videos_view(request):
    """Get all videos for admin review"""
    status_filter = request.GET.get('status', None)

    videos = Video.objects.select_related('founder').prefetch_related('views', 'likes').order_by('-created_at')

    if status_filter and status_filter != 'all':
        videos = videos.filter(status=status_filter)

    videos_data = []
    for video in videos:
        # Get founder's company name if they have a founder profile
        company_name = None
        if hasattr(video.founder, 'founder_profile') and video.founder.founder_profile:
            company_name = video.founder.founder_profile.company_name
        
        videos_data.append({
            'id': str(video.id),
            'title': video.title,
            'url': video.url,
            'thumbnail_url': video.thumbnail_url,
            'duration': video.duration,
            'status': video.status,
            'is_current': video.is_current,
            'view_count': video.views.count(),
            'like_count': video.likes.count(),
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