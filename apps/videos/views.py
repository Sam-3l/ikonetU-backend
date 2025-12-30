from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.db.models import F, Q
from django.core.files.storage import default_storage
from .models import Video, VideoLike, VideoView
from .serializers import VideoSerializer, VideoWithFounderSerializer, VideoHistorySerializer


@api_view(['GET'])
@permission_classes([AllowAny])
def video_feed_view(request):
    """Get video feed - only current ACTIVE videos (approved) with likes and views"""
    limit = int(request.GET.get('limit', 20))
    offset = int(request.GET.get('offset', 0))
    user = request.user if request.user.is_authenticated else None
    
    # Only show current active (approved) videos
    videos = Video.objects.filter(
        status='active',
        is_current=True
    ).select_related('founder').prefetch_related('likes', 'views')
    
    # Get one video per founder (the current one)
    seen_founders = set()
    unique_videos = []
    for video in videos:
        if video.founder_id not in seen_founders:
            unique_videos.append(video)
            seen_founders.add(video.founder_id)
    
    # Apply pagination
    paginated_videos = unique_videos[offset:offset + limit]
    
    # Add like status for authenticated users
    serialized_data = []
    for video in paginated_videos:
        video_data = VideoWithFounderSerializer(video).data
        video_data['likeCount'] = video.likes.count()
        video_data['viewCount'] = video.views.count()
        
        if user:
            video_data['isLiked'] = video.likes.filter(user=user).exists()
        else:
            video_data['isLiked'] = False
            
        serialized_data.append(video_data)
    
    return Response(serialized_data)


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
            video_data = serializer.data
            video_data['likeCount'] = video.likes.count()
            video_data['viewCount'] = video.views.count()
            return Response(video_data)
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
    
    serialized_data = []
    for video in videos:
        video_data = VideoHistorySerializer(video).data
        video_data['likeCount'] = video.likes.count()
        video_data['viewCount'] = video.views.count()
        serialized_data.append(video_data)
    
    return Response(serialized_data)


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
        
        video_data = VideoSerializer(video).data
        video_data['likeCount'] = 0
        video_data['viewCount'] = 0
        
        return Response(video_data, status=status.HTTP_201_CREATED)
        
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
        
        video_data = VideoSerializer(video).data
        video_data['likeCount'] = video.likes.count()
        video_data['viewCount'] = video.views.count()
        
        return Response(video_data)
        
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
        video = Video.objects.select_related('founder').prefetch_related('likes', 'views').get(id=video_id)
        
        if request.method == 'GET':
            serializer = VideoWithFounderSerializer(video)
            video_data = serializer.data
            video_data['likeCount'] = video.likes.count()
            video_data['viewCount'] = video.views.count()
            
            if request.user.is_authenticated:
                video_data['isLiked'] = video.likes.filter(user=request.user).exists()
            else:
                video_data['isLiked'] = False
            
            return Response(video_data)
        
        elif request.method == 'PUT':
            if not request.user.is_authenticated or video.founder != request.user:
                return Response({'message': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)
            
            # Only allow updating title and thumbnail
            allowed_fields = ['title', 'thumbnail_url']
            update_data = {k: v for k, v in request.data.items() if k in allowed_fields}
            
            serializer = VideoSerializer(video, data=update_data, partial=True)
            if serializer.is_valid():
                serializer.save()
                video_data = serializer.data
                video_data['likeCount'] = video.likes.count()
                video_data['viewCount'] = video.views.count()
                return Response(video_data)
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
    except Video.DoesNotExist:
        return Response({'message': 'Video not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def like_video_view(request, video_id):
    """Toggle like on a video, or force like with double_tap param"""
    try:
        video = Video.objects.get(id=video_id)
        is_double_tap = request.data.get('double_tap', False) or request.GET.get('double_tap', False)
        
        # Check if user already liked this video
        existing_like = VideoLike.objects.filter(video=video, user=request.user).first()
        
        if is_double_tap:
            # Double tap always likes (never unlikes)
            if not existing_like:
                VideoLike.objects.create(video=video, user=request.user)
            liked = True
        else:
            if existing_like:
                # Unlike
                existing_like.delete()
                liked = False
            else:
                # Like
                VideoLike.objects.create(video=video, user=request.user)
                liked = True
        
        like_count = video.likes.count()
        
        return Response({
            'liked': liked,
            'likeCount': like_count
        })
        
    except Video.DoesNotExist:
        return Response({'message': 'Video not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([AllowAny])
def track_video_view(request, video_id):
    """Track a video view"""
    try:
        video = Video.objects.get(id=video_id)
        
        # Create view record
        # For authenticated users, track by user
        # For anonymous users, track by session or IP
        if request.user.is_authenticated:
            # Check if user already viewed this video
            existing_view = VideoView.objects.filter(
                video=video, 
                user=request.user
            ).first()
            
            if not existing_view:
                VideoView.objects.create(video=video, user=request.user)
        else:
            # For anonymous users, use session or IP
            session_key = request.session.session_key
            if not session_key:
                request.session.create()
                session_key = request.session.session_key
            
            ip_address = request.META.get('REMOTE_ADDR')
            
            # Check if this session/IP already viewed
            existing_view = VideoView.objects.filter(
                video=video,
                session_key=session_key
            ).first()
            
            if not existing_view:
                VideoView.objects.create(
                    video=video,
                    session_key=session_key,
                    ip_address=ip_address
                )
        
        view_count = video.views.count()
        
        return Response({
            'viewCount': view_count
        })
        
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
        
        video_data = VideoSerializer(video).data
        video_data['likeCount'] = video.likes.count()
        video_data['viewCount'] = video.views.count()
        
        return Response(video_data)
        
    except Video.DoesNotExist:
        return Response({'message': 'Video not found'}, status=status.HTTP_404_NOT_FOUND)