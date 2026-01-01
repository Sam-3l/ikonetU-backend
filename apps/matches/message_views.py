from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q
from django.utils import timezone
from .models import Match, Message


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def match_messages_view(request, match_id):
    """
    Get all messages in a match with delivery status
    Used for: Initial load, pagination, history
    """
    user = request.user
    
    # Pagination params
    limit = int(request.GET.get('limit', 50))
    before = request.GET.get('before')  # Message ID to load messages before
    
    try:
        match = Match.objects.get(
            Q(id=match_id) & (Q(investor=user) | Q(founder=user))
        )
    except Match.DoesNotExist:
        return Response({'message': 'Match not found'}, status=status.HTTP_404_NOT_FOUND)
    
    # Get messages
    messages = Message.objects.filter(match=match)
    
    # Pagination: get messages before specific message
    if before:
        messages = messages.filter(created_at__lt=Message.objects.get(id=before).created_at)
    
    messages_list = messages.order_by('-created_at')[:limit]
    messages_list = list(reversed(messages_list))  # Reverse to chronological order
    
    # First mark 'sent' messages as 'delivered' (recipient has fetched them)
    Message.objects.filter(
        match=match,
        status='sent'
    ).exclude(sender=user).update(
        status='delivered',
        delivered_at=timezone.now()
    )
    
    # Serialize with status - refresh from DB to get updated statuses
    messages_list = Message.objects.filter(
        id__in=[msg.id for msg in messages_list]
    ).order_by('created_at')
    
    data = [{
        'id': str(msg.id),
        'sender_id': str(msg.sender_id),
        'content': msg.content,
        'status': msg.status,
        'delivered_at': msg.delivered_at.isoformat() if msg.delivered_at else None,
        'read_at': msg.read_at.isoformat() if msg.read_at else None,
        'created_at': msg.created_at.isoformat(),
    } for msg in messages_list]
    
    return Response(data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_message_view(request, match_id):
    """
    Send a message via REST API
    Used for: Fallback when WebSocket unavailable
    """
    user = request.user
    content = request.data.get('content', '').strip()
    
    if not content:
        return Response(
            {'message': 'Content is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if len(content) > 5000:
        return Response(
            {'message': 'Message too long (max 5000 characters)'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        match = Match.objects.get(
            Q(id=match_id) & 
            (Q(investor=user) | Q(founder=user)) &
            Q(is_active=True)
        )
    except Match.DoesNotExist:
        return Response(
            {'message': 'Match not found or inactive'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Create message
    message = Message.objects.create(
        match=match,
        sender=user,
        content=content,
        status='sent'
    )
    
    return Response({
        'id': str(message.id),
        'sender_id': str(message.sender_id),
        'content': message.content,
        'status': message.status,
        'delivered_at': None,
        'read_at': None,
        'created_at': message.created_at.isoformat(),
    }, status=status.HTTP_201_CREATED)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def mark_messages_read_view(request, match_id):
    """
    Mark all messages in match as read
    Used for: When user is actively viewing the chat
    """
    user = request.user
    
    try:
        match = Match.objects.get(
            Q(id=match_id) & (Q(investor=user) | Q(founder=user))
        )
    except Match.DoesNotExist:
        return Response({'message': 'Match not found'}, status=status.HTTP_404_NOT_FOUND)
    
    # First mark 'sent' as 'delivered' if not already
    Message.objects.filter(
        match=match,
        status='sent'
    ).exclude(sender=user).update(
        status='delivered',
        delivered_at=timezone.now()
    )
    
    # Then mark 'delivered' and 'sent' as 'read'
    messages_to_read = Message.objects.filter(
        match=match,
        status__in=['sent', 'delivered']
    ).exclude(sender=user)
    
    updated_count = messages_to_read.update(
        status='read',
        read_at=timezone.now()
    )
    
    return Response({
        'marked_read': updated_count,
        'message_ids': list(messages_to_read.values_list('id', flat=True))
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_messages_delivered_view(request, match_id):
    """
    Mark messages as delivered when recipient loads the chat
    Separate from marking as read
    """
    user = request.user
    
    try:
        match = Match.objects.get(
            Q(id=match_id) & (Q(investor=user) | Q(founder=user))
        )
    except Match.DoesNotExist:
        return Response({'message': 'Match not found'}, status=status.HTTP_404_NOT_FOUND)
    
    # Mark 'sent' messages as 'delivered'
    messages_to_deliver = Message.objects.filter(
        match=match,
        status='sent'
    ).exclude(sender=user)
    
    message_ids = list(messages_to_deliver.values_list('id', flat=True))
    
    updated_count = messages_to_deliver.update(
        status='delivered',
        delivered_at=timezone.now()
    )
    
    # Broadcast delivery status via WebSocket
    if updated_count > 0:
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync
        
        channel_layer = get_channel_layer()
        room_group_name = f'chat_{match_id}'
        
        for message_id in message_ids:
            async_to_sync(channel_layer.group_send)(
                room_group_name,
                {
                    'type': 'message_status_update',
                    'message_id': str(message_id),
                    'status': 'delivered',
                }
            )
    
    return Response({
        'marked_delivered': updated_count,
        'message_ids': [str(mid) for mid in message_ids]
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def unread_count_view(request):
    """
    Get total unread message count across all matches
    Used for: Badge notifications
    """
    user = request.user
    
    # Get user's matches
    if user.role == 'investor':
        matches = Match.objects.filter(investor=user, is_active=True)
    else:
        matches = Match.objects.filter(founder=user, is_active=True)
    
    # Count unread messages
    unread_count = Message.objects.filter(
        match__in=matches,
        status__in=['sent', 'delivered']
    ).exclude(sender=user).count()
    
    return Response({'unread_count': unread_count})