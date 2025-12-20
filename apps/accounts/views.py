from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth import authenticate
from django.core.cache import cache
from .serializers import RegisterSerializer, UserSerializer
from .models import User
import secrets

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