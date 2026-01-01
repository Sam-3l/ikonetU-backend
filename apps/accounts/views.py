from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth import authenticate
from django.core.cache import cache
from apps.videos.models import Video, VideoLike, VideoView
from apps.profiles.models import FounderProfile, InvestorProfile
from apps.profiles.serializers import FounderProfileSerializer, InvestorProfileSerializer
from .serializers import RegisterSerializer, UserSerializer
from .models import User
import secrets

from django.http import FileResponse, Http404
from django.conf import settings
import os
import mimetypes


def generate_token():
    return secrets.token_urlsafe(32)

@api_view(['POST'])
@permission_classes([AllowAny])
def register_view(request):
    """
    Register a new user
    """
    serializer = RegisterSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        
        # Create profile based on role
        if user.role == 'founder':
            from apps.profiles.models import FounderProfile
            FounderProfile.objects.create(user=user, company_name='')
        elif user.role == 'investor':
            from apps.profiles.models import InvestorProfile
            InvestorProfile.objects.create(user=user)
        
        # Generate token and store in cache
        token = generate_token()
        cache.set(f'auth_token:{token}', user.id, timeout=604800)  # 7 days
        
        user_serializer = UserSerializer(user)
        return Response({
            'user': user_serializer.data,
            'token': token
        }, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    """
    Login user
    """
    email = request.data.get('email')
    password = request.data.get('password')
    
    if not email or not password:
        return Response({'error': 'Email and password required'}, status=status.HTTP_400_BAD_REQUEST)
    
    user = authenticate(request, username=email, password=password)
    
    if user is None:
        return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
    
    # Generate token and store in cache
    token = generate_token()
    cache.set(f'auth_token:{token}', user.id, timeout=604800)  # 7 days
    
    user_serializer = UserSerializer(user)
    return Response({
        'user': user_serializer.data,
        'token': token
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    """
    Logout user
    """
    # Remove token from cache
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if token:
        cache.delete(f'auth_token:{token}')
    
    return Response({'message': 'Logged out successfully'})

@api_view(['GET'])
@permission_classes([AllowAny])
def me_view(request):
    """
    Get current user details with profile
    """
    if not request.user.is_authenticated:
        return Response({'message': 'Not authenticated'}, status=status.HTTP_401_UNAUTHORIZED)
    
    user_serializer = UserSerializer(request.user)
    profile = None
    
    if request.user.role == 'founder':
        from apps.profiles.models import FounderProfile
        from apps.profiles.serializers import FounderProfileSerializer
        try:
            founder_profile = FounderProfile.objects.get(user=request.user)
            profile = FounderProfileSerializer(founder_profile).data
        except FounderProfile.DoesNotExist:
            pass
    elif request.user.role == 'investor':
        from apps.profiles.models import InvestorProfile
        from apps.profiles.serializers import InvestorProfileSerializer
        try:
            investor_profile = InvestorProfile.objects.get(user=request.user)
            profile = InvestorProfileSerializer(investor_profile).data
        except InvestorProfile.DoesNotExist:
            pass
    
    return Response({
        'user': user_serializer.data,
        'profile': profile
    })    

@api_view(['GET'])
@permission_classes([AllowAny])
def get_user_profile(request, user_id):
    try:
        user = User.objects.get(id=user_id)
        
        if user.role == 'founder':
            profile = FounderProfile.objects.get(user=user)
            profile_data = FounderProfileSerializer(profile).data
            
            # Get current active/processing video (is_current=True)
            current_video = Video.objects.filter(
                founder=user,
                is_current=True,
                status__in=['active', 'processing']
            ).first()
            
            video_data = None
            if current_video:
                # Check if requesting user has liked this video
                is_liked = False
                if request.user.is_authenticated:
                    is_liked = VideoLike.objects.filter(
                        video=current_video,
                        user=request.user
                    ).exists()
                
                # Get like and view counts
                like_count = VideoLike.objects.filter(video=current_video).count()
                view_count = VideoView.objects.filter(video=current_video).count()
                
                video_data = {
                    'id': str(current_video.id),
                    'url': current_video.url,
                    'thumbnailUrl': current_video.thumbnail_url,
                    'title': current_video.title,
                    'duration': current_video.duration,
                    'status': current_video.status,
                    'viewCount': view_count,
                    'likeCount': like_count,
                    'isLiked': is_liked,
                    'createdAt': current_video.created_at.isoformat(),
                }
        else:
            profile = InvestorProfile.objects.get(user=user)
            profile_data = InvestorProfileSerializer(profile).data
            video_data = None
            
        return Response({
            'role': user.role,
            'name': user.name,
            'avatarUrl': user.avatar_url,
            'founderProfile': profile_data if user.role == 'founder' else None,
            'investorProfile': profile_data if user.role == 'investor' else None,
            'currentVideo': video_data
        })
    except (User.DoesNotExist, FounderProfile.DoesNotExist, InvestorProfile.DoesNotExist):
        return Response({'message': 'Profile not found'}, status=404)