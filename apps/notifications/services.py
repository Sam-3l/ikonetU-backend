from .models import Notification
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync


class NotificationService:
    """Service for creating and sending notifications"""
    
    @staticmethod
    def create_match_notification(match):
        """Create notification for new match"""
        # Notify founder
        founder_notification = Notification.objects.create(
            recipient=match.founder,
            notification_type='match',
            title='New Match! 🎉',
            message=f'{match.investor.name} is interested in connecting with you!',
            related_user=match.investor,
            related_match_id=match.id,
            action_url=f'/matches'
        )
        
        # Send real-time notification to founder
        NotificationService._send_realtime(match.founder.id, founder_notification)
        
        return founder_notification
    
    @staticmethod
    def create_message_notification(message, match):
        """Create notification for new message"""
        # Determine recipient (the person who didn't send the message)
        recipient = match.founder if message.sender == match.investor else match.investor
        
        notification = Notification.objects.create(
            recipient=recipient,
            notification_type='message',
            title=f'New message from {message.sender.name}',
            message=message.content[:100],  # Preview
            related_user=message.sender,
            related_match_id=match.id,
            related_message_id=message.id,
            action_url=f'/messages'
        )
        
        # Send real-time notification
        NotificationService._send_realtime(recipient.id, notification)
        
        return notification
    
    @staticmethod
    def create_video_status_notification(video, status):
        """Create notification for video approval/rejection"""
        notification_type = 'video_approved' if status == 'active' else 'video_rejected'
        
        if status == 'active':
            title = 'Video Approved! ✅'
            message = 'Your pitch video has been approved and is now live!'
        else:
            title = 'Video Requires Changes'
            message = 'Your pitch video needs some adjustments. Please check the feedback.'
        
        notification = Notification.objects.create(
            recipient=video.founder,
            notification_type=notification_type,
            title=title,
            message=message,
            related_video_id=video.id,
            action_url='/profile'
        )
        
        # Send real-time notification
        NotificationService._send_realtime(video.founder.id, notification)
        
        return notification
    
    @staticmethod
    def _send_realtime(user_id, notification):
        """Send real-time notification via WebSocket"""
        channel_layer = get_channel_layer()
        if channel_layer:
            try:
                async_to_sync(channel_layer.group_send)(
                    f"user_{user_id}",
                    {
                        'type': 'notification_message',
                        'notification': {
                            'id': str(notification.id),
                            'type': notification.notification_type,
                            'title': notification.title,
                            'message': notification.message,
                            'action_url': notification.action_url,
                            'is_read': notification.is_read,
                            'created_at': notification.created_at.isoformat(),
                        }
                    }
                )
            except Exception as e:
                print(f"Failed to send real-time notification: {e}")