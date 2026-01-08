import uuid
from django.db import models
from apps.accounts.models import User


class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('match', 'New Match'),
        ('message', 'New Message'),
        ('video_approved', 'Video Approved'),
        ('video_rejected', 'Video Rejected'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=255)
    message = models.TextField()
    
    # Related objects (nullable for flexibility)
    related_user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='notifications_triggered')
    related_match_id = models.UUIDField(null=True, blank=True)
    related_message_id = models.UUIDField(null=True, blank=True)
    related_video_id = models.UUIDField(null=True, blank=True)
    
    # Action URL (where to navigate when clicked)
    action_url = models.CharField(max_length=255, null=True, blank=True)
    
    # Status
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'notifications'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', '-created_at']),
            models.Index(fields=['recipient', 'is_read']),
        ]
    
    def __str__(self):
        return f"{self.notification_type} for {self.recipient.name}"
    
    def mark_as_read(self):
        if not self.is_read:
            from django.utils import timezone
            self.is_read = True
            self.read_at = timezone.now()
            self.save()