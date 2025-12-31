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
    """Messages between matched users"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='messages_sent')
    content = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'messages'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['match', 'created_at']),
            models.Index(fields=['sender', 'is_read']),
        ]

    def __str__(self):
        return f"{self.sender.name} in {self.match.id}"