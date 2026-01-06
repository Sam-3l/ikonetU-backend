from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework import status
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.db.models import Count, Q
from PIL import Image
from io import BytesIO
import uuid

from .models import FounderProfile, InvestorProfile
from .serializers import FounderProfileSerializer, InvestorProfileSerializer
from apps.accounts.serializers import UserSerializer
from apps.videos.models import Video, VideoView, VideoLike
from apps.matches.models import Match


@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
def founder_profile_view(request):
    """Get or update current user's founder profile"""
    try:
        profile = FounderProfile.objects.get(user=request.user)
    except FounderProfile.DoesNotExist:
        return Response({'message': 'Profile not found'}, status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        serializer = FounderProfileSerializer(profile)
        return Response(serializer.data)
    
    elif request.method == 'PUT':
        serializer = FounderProfileSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
def investor_profile_view(request):
    """Get or update current user's investor profile"""
    try:
        profile = InvestorProfile.objects.get(user=request.user)
    except InvestorProfile.DoesNotExist:
        return Response({'message': 'Profile not found'}, status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        serializer = InvestorProfileSerializer(profile)
        return Response(serializer.data)
    
    elif request.method == 'PUT':
        serializer = InvestorProfileSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def upload_avatar(request):
    """Upload and process user avatar"""
    if 'avatar' not in request.FILES:
        return Response({'message': 'No avatar file provided'}, status=status.HTTP_400_BAD_REQUEST)
    
    avatar_file = request.FILES['avatar']
    
    # Validate file type
    allowed_types = ['image/jpeg', 'image/png', 'image/jpg', 'image/webp']
    if avatar_file.content_type not in allowed_types:
        return Response(
            {'message': 'Invalid file type. Only JPEG, PNG, and WebP are allowed.'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Validate file size (max 5MB)
    if avatar_file.size > 5 * 1024 * 1024:
        return Response(
            {'message': 'File too large. Maximum size is 5MB.'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        # Open and process image
        img = Image.open(avatar_file)
        
        # Convert to RGB if necessary
        if img.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = background
        
        # Resize to 400x400 (square)
        img.thumbnail((400, 400), Image.Resampling.LANCZOS)
        
        # Save to BytesIO
        output = BytesIO()
        img.save(output, format='JPEG', quality=90, optimize=True)
        output.seek(0)
        
        # Delete old avatar if exists
        if request.user.avatar_url:
            # Extract just the path part from the URL
            try:
                # Parse the URL to get just the file path
                from urllib.parse import urlparse
                parsed = urlparse(request.user.avatar_url)
                old_path = parsed.path.split('/media/')[-1] if '/media/' in parsed.path else parsed.path.lstrip('/')
                if old_path and default_storage.exists(old_path):
                    default_storage.delete(old_path)
            except Exception:
                pass  # If deletion fails, continue with upload
        
        # Generate unique filename
        filename = f"avatars/{request.user.id}/{uuid.uuid4()}.jpg"
        
        # Save new avatar
        path = default_storage.save(filename, ContentFile(output.read()))
        
        # Get the full URL from storage backend (S3, CloudFront, etc.)
        avatar_url = request.build_absolute_uri(default_storage.url(path))
        
        # Update user avatar_url
        request.user.avatar_url = avatar_url
        request.user.save()
        
        return Response({
            'message': 'Avatar uploaded successfully',
            'avatar_url': request.user.avatar_url
        })
        
    except Exception as e:
        return Response(
            {'message': f'Failed to process image: {str(e)}'}, 
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def profile_stats_view(request):
    """Get profile statistics for current user"""
    user = request.user
    
    if user.role == 'founder':
        # Get all videos for this founder
        videos = Video.objects.filter(founder=user)
        
        # Total views across all videos
        total_views = VideoView.objects.filter(video__founder=user).count()
        
        # Total likes across all videos
        total_likes = VideoLike.objects.filter(video__founder=user).count()
        
        # Get matches
        matches = Match.objects.filter(
            Q(founder=user) | Q(investor=user)
        )
        
        # Active matches (accepted by investor)
        active_matches = matches.filter(is_active=True).count()
        
        # Interested count (all matches including pending)
        interested_count = matches.count()
        
        # Video count
        video_count = videos.count()
        
        # Response rate calculation
        response_rate = 0
        if interested_count > 0:
            response_rate = round((active_matches / interested_count) * 100)
        
        return Response({
            'totalViews': total_views,
            'totalLikes': total_likes,
            'activeMatches': active_matches,
            'interestedCount': interested_count,
            'videoCount': video_count,
            'responseRate': response_rate
        })
    
    else:  # investor
        # Get matches where user is investor
        matches = Match.objects.filter(investor=user)
        
        # Active matches
        active_matches = matches.filter(is_active=True).count()
        
        # Total matches (including pending)
        total_matches = matches.count()
        
        # Interested founders (total matches)
        interested_count = total_matches
        
        return Response({
            'activeMatches': active_matches,
            'interestedCount': interested_count,
            'totalMatches': total_matches
        })