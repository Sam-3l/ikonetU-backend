from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from .models import Notification
from rest_framework.permissions import AllowAny
from django.core.mail import send_mail
from django.conf import settings


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def notifications_list_view(request):
    """Get all notifications for current user"""
    notifications = Notification.objects.filter(
        recipient=request.user
    ).select_related('related_user')[:50]
    
    data = [{
        'id': str(n.id),
        'type': n.notification_type,
        'title': n.title,
        'message': n.message,
        'related_user': {
            'id': str(n.related_user.id),
            'name': n.related_user.name,
            'avatar_url': n.related_user.avatar_url,
        } if n.related_user else None,
        'action_url': n.action_url,
        'is_read': n.is_read,
        'read_at': n.read_at.isoformat() if n.read_at else None,
        'created_at': n.created_at.isoformat(),
    } for n in notifications]
    
    return Response(data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def unread_count_view(request):
    """Get unread notification count"""
    count = Notification.objects.filter(
        recipient=request.user,
        is_read=False
    ).count()
    
    return Response({'count': count})


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def mark_notification_read_view(request, notification_id):
    """Mark a notification as read"""
    try:
        notification = Notification.objects.get(
            id=notification_id,
            recipient=request.user
        )
        notification.mark_as_read()
        return Response({'success': True})
    except Notification.DoesNotExist:
        return Response(
            {'error': 'Notification not found'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def mark_all_read_view(request):
    """Mark all notifications as read"""
    Notification.objects.filter(
        recipient=request.user,
        is_read=False
    ).update(is_read=True, read_at=timezone.now())
    
    return Response({'success': True})


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_notification_view(request, notification_id):
    """Delete a notification"""
    try:
        notification = Notification.objects.get(
            id=notification_id,
            recipient=request.user
        )
        notification.delete()
        return Response({'success': True})
    except Notification.DoesNotExist:
        return Response(
            {'error': 'Notification not found'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def clear_all_notifications_view(request):
    """Clear all notifications"""
    Notification.objects.filter(recipient=request.user).delete()
    return Response({'success': True})


@api_view(["POST"])
@permission_classes([AllowAny])
def judge_application(request):
    data = request.data

    message = f"""
New Judge Application

Full Name: {data.get('full_name')}
Email: {data.get('email')}
LinkedIn: {data.get('linkedin')}
Role & Company: {data.get('role')}
Industry: {data.get('industry')}
Experience: {data.get('experience')}

Motivation:
{data.get('motivation')}

Perspective:
{data.get('perspective')}

Invested Before:
{data.get('invested')}
"""

    send_mail(
        subject="New Judge Application | IkonetU",
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=["customer.service@ikonetu.com"],
        fail_silently=False,
    )

    return Response({"success": True})
