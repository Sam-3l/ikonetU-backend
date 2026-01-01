from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from .models import Signal
from apps.matches.models import Match
from apps.accounts.models import User


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_signal_view(request):
    """
    Create a signal (swipe action)
    Creates PENDING match if investor shows interest
    """
    investor = request.user
    
    if investor.role != 'investor':
        return Response(
            {'message': 'Only investors can send signals'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    founder_id = request.data.get('founder_id')
    video_id = request.data.get('video_id')
    signal_type = request.data.get('type')
    
    if not all([founder_id, video_id, signal_type]):
        return Response(
            {'message': 'founder_id, video_id, and type are required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if signal_type not in ['interested', 'maybe', 'pass']:
        return Response(
            {'message': 'Invalid signal type'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        founder = User.objects.get(id=founder_id, role='founder')
    except User.DoesNotExist:
        return Response({'message': 'Founder not found'}, status=status.HTTP_404_NOT_FOUND)
    
    # Create or update signal
    with transaction.atomic():
        signal, created = Signal.objects.update_or_create(
            investor=investor,
            founder=founder,
            defaults={
                'video_id': video_id,
                'type': signal_type
            }
        )
        
        # Create PENDING match if interested
        match_created = False
        if signal_type == 'interested':
            match, match_created = Match.objects.get_or_create(
                investor=investor,
                founder=founder,
                defaults={'is_active': False}
            )
    
    return Response({
        'signal': {
            'id': str(signal.id),
            'type': signal.type,
            'created': created
        },
        'match_created': match_created
    }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_signals_view(request):
    """Get signals I've sent (for investors) or received (for founders)"""
    user = request.user
    
    if user.role == 'investor':
        # Get signals I sent
        signals = Signal.objects.filter(investor=user).select_related('founder', 'video')
        data = [{
            'id': s.id,
            'founder': {
                'id': s.founder.id,
                'name': s.founder.name,
            },
            'type': s.type,
            'created_at': s.created_at
        } for s in signals]
    else:
        # Get signals I received
        signals = Signal.objects.filter(founder=user).select_related('investor')
        data = [{
            'id': s.id,
            'investor': {
                'id': s.investor.id,
                'name': s.investor.name,
            },
            'type': s.type,
            'created_at': s.created_at
        } for s in signals]
    
    return Response(data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def signals_received_view(request):
    """Get signals received (founders only)"""
    if request.user.role != 'founder':
        return Response(
            {'message': 'Only founders can view received signals'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    signals = Signal.objects.filter(
        founder=request.user
    ).select_related('investor').order_by('-created_at')
    
    data = [{
        'id': s.id,
        'investor': {
            'id': s.investor.id,
            'name': s.investor.name,
            'avatar_url': s.investor.avatar_url,
        },
        'type': s.type,
        'created_at': s.created_at
    } for s in signals]
    
    return Response(data)