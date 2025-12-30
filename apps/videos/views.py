from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.db.models import F
from django.core.files.storage import default_storage
from .models import Video
from .serializers import VideoSerializer, VideoWithFounderSerializer, VideoHistorySerializer


@api_view(['GET'])
@permission_classes([AllowAny])
def video_feed_view(request):
    """Get video feed - only current ACTIVE videos (approved)"""
    limit = int(request.GET.get('limit', 20))
    offset = int(request.GET.get('offset', 0))
    
    # Only show current active (approved) videos
    videos = Video.objects.filter(
        status='active',
        is_current=True
    ).select_related('founder')
    
    # Get one video per founder (the current one)
    seen_founders = set()
    unique_videos = []
    for video in videos:
        if video.founder_id not in seen_founders:
            unique_videos.append(video)
            seen_founders.add(video.founder_id)
    
    # Apply pagination
    paginated_videos = unique_videos[offset:offset + limit]
    serializer = VideoWithFounderSerializer(paginated_videos, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_videos_view(request):
    """Get current user's current video (can be processing/active/rejected)"""
    try:
        video = Video.objects.filter(
            founder=request.user,
            is_current=True,
            status__in=['processing', 'active', 'rejected']
        ).first()
        
        if video:
            serializer = VideoSerializer(video)
            return Response(serializer.data)
        else:
            return Response(None, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def video_history_view(request):
    """Get all user's videos (current + archived, excludes deleted)"""
    videos = Video.objects.filter(
        founder=request.user
    ).exclude(status='deleted').order_by('-created_at')
    
    serializer = VideoHistorySerializer(videos, many=True)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_video_view(request):
    """
    Create new video (founders only) - automatically sets as current, status=processing
    
    NOTE: Video is saved as-is. Trim parameters are for reference only.
    If you need actual trimming, install FFmpeg on your server.
    """
    if request.user.role != 'founder':
        return Response({'message': 'Only founders can upload videos'}, status=status.HTTP_403_FORBIDDEN)
    
    video_file = request.FILES.get('video_file')
    
    if not video_file:
        return Response({'message': 'video_file is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Save video directly - no trimming
        file_name = f"videos/{request.user.id}/{video_file.name}"
        file_path = default_storage.save(file_name, video_file)
        full_url = request.build_absolute_uri(default_storage.url(file_path))
        
        # Create video record with trim metadata
        video = Video.objects.create(
            founder=request.user,
            url=full_url,
            thumbnail_url=request.data.get('thumbnail_url', ''),
            title=request.data.get('title', video_file.name),
            duration=request.data.get('duration'),
            status='processing',
            is_current=True
        )
        
        return Response(VideoSerializer(video).data, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response(
            {'message': f'Video upload failed: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def set_video_as_current_view(request, video_id):
    """Set an archived video as current (reactivate from history)"""
    try:
        video = Video.objects.get(id=video_id, founder=request.user)
        
        if video.status == 'deleted':
            return Response(
                {'message': 'Cannot activate deleted video'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if video.is_current:
            return Response(
                {'message': 'This video is already current'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Set as current and change status to processing (needs re-approval)
        video.status = 'processing'
        video.is_current = True
        video.save()  # Will archive the previous current video
        
        return Response(VideoSerializer(video).data)
        
    except Video.DoesNotExist:
        return Response({'message': 'Video not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_video_view(request, video_id):
    """Soft delete a video (only archived videos can be deleted)"""
    try:
        video = Video.objects.get(id=video_id, founder=request.user)
        
        if video.is_current:
            return Response(
                {'message': 'Cannot delete current video. Upload a new one first.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if video.status == 'deleted':
            return Response(
                {'message': 'Video already deleted'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        video.status = 'deleted'
        video.save()
        
        return Response({'message': 'Video deleted successfully'})
        
    except Video.DoesNotExist:
        return Response({'message': 'Video not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET', 'PUT'])
@permission_classes([AllowAny])
def video_detail_and_update_view(request, video_id):
    """Get specific video or update video details"""
    try:
        video = Video.objects.select_related('founder').get(id=video_id)
        
        if request.method == 'GET':
            # Increment view count only for active current videos
            if video.status == 'active' and video.is_current:
                Video.objects.filter(id=video_id).update(view_count=F('view_count') + 1)
                video.refresh_from_db()
            
            serializer = VideoWithFounderSerializer(video)
            return Response(serializer.data)
        
        elif request.method == 'PUT':
            if not request.user.is_authenticated or video.founder != request.user:
                return Response({'message': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)
            
            # Only allow updating title and thumbnail
            allowed_fields = ['title', 'thumbnail_url']
            update_data = {k: v for k, v in request.data.items() if k in allowed_fields}
            
            serializer = VideoSerializer(video, data=update_data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
    except Video.DoesNotExist:
        return Response({'message': 'Video not found'}, status=status.HTTP_404_NOT_FOUND)


# Admin endpoints (for approving/rejecting videos)
@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def admin_update_video_status_view(request, video_id):
    """Admin: Approve or reject video"""
    if request.user.role != 'admin':
        return Response({'message': 'Admin only'}, status=status.HTTP_403_FORBIDDEN)
    
    try:
        video = Video.objects.get(id=video_id)
        new_status = request.data.get('status')
        
        if new_status not in ['active', 'rejected']:
            return Response(
                {'message': 'Status must be "active" or "rejected"'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        video.status = new_status
        video.save()
        
        return Response(VideoSerializer(video).data)
        
    except Video.DoesNotExist:
        return Response({'message': 'Video not found'}, status=status.HTTP_404_NOT_FOUND)