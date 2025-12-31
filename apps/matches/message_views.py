from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q
from .models import Match, Message


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def match_messages_view(request, match_id):
    """Get all messages in a match"""
    user = request.user
    
    try:
        # Verify user is part of match
        match = Match.objects.get(
            Q(id=match_id) & (Q(investor=user) | Q(founder=user))
        )
    except Match.DoesNotExist:
        return Response({'message': 'Match not found'}, status=status.HTTP_404_NOT_FOUND)
    
    # Get messages
    messages = Message.objects.filter(match=match).order_by('created_at')
    
    # Mark messages as read
    Message.objects.filter(
        match=match,
        is_read=False
    ).exclude(sender=user).update(is_read=True)
    
    # Serialize
    data = [{
        'id': msg.id,
        'sender_id': msg.sender_id,
        'content': msg.content,
        'is_read': msg.is_read,
        'created_at': msg.created_at,
    } for msg in messages]
    
    return Response(data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_message_view(request, match_id):
    """Send a message in a match"""
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
        # Verify user is part of match and it's active
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
        content=content
    )
    
    return Response({
        'id': message.id,
        'sender_id': message.sender_id,
        'content': message.content,
        'is_read': message.is_read,
        'created_at': message.created_at,
    }, status=status.HTTP_201_CREATED)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def mark_messages_read_view(request, match_id):
    """Mark all messages in match as read"""
    user = request.user
    
    try:
        match = Match.objects.get(
            Q(id=match_id) & (Q(investor=user) | Q(founder=user))
        )
    except Match.DoesNotExist:
        return Response({'message': 'Match not found'}, status=status.HTTP_404_NOT_FOUND)
    
    # Mark all messages from other user as read
    updated = Message.objects.filter(
        match=match,
        is_read=False
    ).exclude(sender=user).update(is_read=True)
    
    return Response({'marked_read': updated})