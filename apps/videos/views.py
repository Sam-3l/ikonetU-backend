from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.db.models import F
from .models import Video
from .serializers import VideoSerializer, VideoWithFounderSerializer


@api_view(['GET'])
@permission_classes([AllowAny])
def video_feed_view(request):
    """Get video feed (filtered for investors, all active for others)"""
    limit = int(request.GET.get('limit', 20))
    offset = int(request.GET.get('offset', 0))
    
    videos = Video.objects.filter(status='active').select_related('founder')
    
    # TODO: Add filtering based on investor preferences later
    
    videos = videos[offset:offset + limit]
    serializer = VideoWithFounderSerializer(videos, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_videos_view(request):
    """Get current user's videos"""
    videos = Video.objects.filter(founder=request.user)
    serializer = VideoSerializer(videos, many=True)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_video_view(request):
    """Create new video (founders only)"""
    if request.user.role != 'founder':
        return Response({'message': 'Only founders can upload videos'}, status=status.HTTP_403_FORBIDDEN)
    
    data = request.data.copy()
    data['founder'] = request.user.id
    
    serializer = VideoSerializer(data=data)
    if serializer.is_valid():
        video = serializer.save(founder=request.user)
        return Response(VideoSerializer(video).data, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# apps/videos/views.py - Replace video_detail_view and update_video_view with this:

@api_view(['GET', 'PUT'])
@permission_classes([AllowAny])
def video_detail_and_update_view(request, video_id):
    """Get specific video, increment view count, or update video"""
    try:
        video = Video.objects.select_related('founder').get(id=video_id)
        
        if request.method == 'GET':
            # Increment view count
            Video.objects.filter(id=video_id).update(view_count=F('view_count') + 1)
            video.refresh_from_db()
            
            serializer = VideoWithFounderSerializer(video)
            return Response(serializer.data)
        
        elif request.method == 'PUT':
            # Check authorization
            if not request.user.is_authenticated or video.founder != request.user:
                return Response({'message': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)
            
            serializer = VideoSerializer(video, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
    except Video.DoesNotExist:
        return Response({'message': 'Video not found'}, status=status.HTTP_404_NOT_FOUND)