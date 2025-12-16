from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Count, Q
from .models import Video
from .serializers import VideoWithFounderSerializer
from apps.accounts.models import User
from apps.accounts.serializers import UserSerializer
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
    
    total_users = User.objects.count()
    total_founders = User.objects.filter(role='founder').count()
    total_investors = User.objects.filter(role='investor').count()
    
    total_videos = Video.objects.count()
    active_videos = Video.objects.filter(status='active', is_current=True).count()
    pending_videos = Video.objects.filter(status='processing', is_current=True).count()
    
    pending_reports = Report.objects.filter(status='pending').count()
    
    return Response({
        'totalUsers': total_users,
        'totalFounders': total_founders,
        'totalInvestors': total_investors,
        'totalVideos': total_videos,
        'activeVideos': active_videos,
        'pendingVideos': pending_videos,
        'pendingReports': pending_reports,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@require_admin
def admin_users_view(request):
    """Get all users"""
    users = User.objects.all().order_by('-created_at')
    
    users_data = []
    for user in users:
        users_data.append({
            'id': user.id,
            'name': user.name,
            'email': user.email,
            'role': user.role,
            'created_at': user.created_at,
            'onboarding_complete': user.onboarding_complete,
        })
    
    return Response(users_data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@require_admin
def admin_videos_view(request):
    """Get all videos for admin review"""
    status_filter = request.GET.get('status', None)
    
    videos = Video.objects.select_related('founder').order_by('-created_at')
    
    if status_filter:
        videos = videos.filter(status=status_filter)
    
    videos_data = []
    for video in videos:
        videos_data.append({
            'id': video.id,
            'title': video.title,
            'url': video.url,
            'thumbnail_url': video.thumbnail_url,
            'duration': video.duration,
            'status': video.status,
            'is_current': video.is_current,
            'view_count': video.view_count,
            'created_at': video.created_at,
            'founder': {
                'id': video.founder.id,
                'name': video.founder.name,
                'email': video.founder.email,
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
            'video': {
                'id': video.id,
                'status': video.status,
            }
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
            'video': {
                'id': video.id,
                'status': video.status,
            }
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
            return Response(
                {'message': 'Cannot delete admin users'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        user.is_active = False
        user.save()
        
        return Response({'message': 'User deactivated successfully'})
    except User.DoesNotExist:
        return Response({'message': 'User not found'}, status=status.HTTP_404_NOT_FOUND)