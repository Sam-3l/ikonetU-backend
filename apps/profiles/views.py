from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from .models import FounderProfile, InvestorProfile
from .serializers import FounderProfileSerializer, InvestorProfileSerializer
from apps.accounts.serializers import UserSerializer


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


@api_view(['GET'])
@permission_classes([AllowAny])
def founder_profile_detail_view(request, user_id):
    """Get specific founder's profile by user ID"""
    try:
        profile = FounderProfile.objects.get(user__id=user_id)
        user = profile.user
        
        profile_data = FounderProfileSerializer(profile).data
        user_data = UserSerializer(user).data
        
        return Response({
            'profile': profile_data,
            'user': {
                'id': user_data['id'],
                'name': user_data['name'],
                'avatar_url': user_data.get('avatar_url')
            }
        })
    except FounderProfile.DoesNotExist:
        return Response({'message': 'Profile not found'}, status=status.HTTP_404_NOT_FOUND)


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


@api_view(['GET'])
@permission_classes([AllowAny])
def investor_profile_detail_view(request, user_id):
    """Get specific investor's profile by user ID"""
    try:
        profile = InvestorProfile.objects.get(user__id=user_id)
        user = profile.user
        
        profile_data = InvestorProfileSerializer(profile).data
        user_data = UserSerializer(user).data
        
        return Response({
            'profile': profile_data,
            'user': {
                'id': user_data['id'],
                'name': user_data['name'],
                'avatar_url': user_data.get('avatar_url')
            }
        })
    except InvestorProfile.DoesNotExist:
        return Response({'message': 'Profile not found'}, status=status.HTTP_404_NOT_FOUND)