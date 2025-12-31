import uuid
from django.db import models
from apps.accounts.models import User


class Match(models.Model):
    """Represents a match between investor and founder"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    investor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='investor_matches')
    founder = models.ForeignKey(User, on_delete=models.CASCADE, related_name='founder_matches')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'matches'
        ordering = ['-created_at']
        unique_together = ('investor', 'founder')
        indexes = [
            models.Index(fields=['investor', 'is_active']),
            models.Index(fields=['founder', 'is_active']),
        ]

    def __str__(self):
        return f"Match: {self.investor.name} ↔ {self.founder.name}"


class Message(models.Model):
    """Messages between matched users with delivery tracking"""
    
    STATUS_CHOICES = [
        ('sent', 'Sent'),           # Message sent from sender
        ('delivered', 'Delivered'),  # Message reached recipient's device
        ('read', 'Read'),            # Message opened/read by recipient
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='messages_sent')
    content = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='sent')
    delivered_at = models.DateTimeField(null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'messages'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['match', 'created_at']),
            models.Index(fields=['sender', 'status']),
            models.Index(fields=['match', 'status']),
        ]

    def __str__(self):
        return f"{self.sender.name} in {self.match.id}: {self.status}"

    def mark_delivered(self):
        """Mark message as delivered"""
        from django.utils import timezone
        if self.status == 'sent':
            self.status = 'delivered'
            self.delivered_at = timezone.now()
            self.save()

    def mark_read(self):
        """Mark message as read"""
        from django.utils import timezone
        if self.status in ['sent', 'delivered']:
            self.status = 'read'
            self.read_at = timezone.now()
            self.save()