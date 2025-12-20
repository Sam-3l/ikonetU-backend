from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth import login, logout
from .serializers import RegisterSerializer, LoginSerializer, UserSerializer
from .models import User


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
        
        login(request, user)
        user_serializer = UserSerializer(user)
        return Response(user_serializer.data, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):

    print(f"=== LOGIN REQUEST ===")
    print(f"Request headers: {request.headers}")
    print(f"Request origin: {request.headers.get('origin')}")
    
    """
    Login user
    """
    serializer = LoginSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.validated_data['user']
        login(request, user)
        user_serializer = UserSerializer(user)
        return Response(user_serializer.data)
    
    return Response(serializer.errors, status=status.HTTP_401_UNAUTHORIZED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    """
    Logout user
    """
    logout(request)
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
