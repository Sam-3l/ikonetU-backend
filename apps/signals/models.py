import uuid
from django.db import models
from apps.accounts.models import User
from apps.videos.models import Video


class Signal(models.Model):
    """Track investor interactions with founder videos"""
    SIGNAL_CHOICES = [
        ('interested', 'Interested'),  # Heart - strong positive
        ('maybe', 'Maybe'),            # Bookmark - moderate positive
        ('pass', 'Pass'),              # X - negative
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    investor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='signals_sent')
    founder = models.ForeignKey(User, on_delete=models.CASCADE, related_name='signals_received')
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name='signals')
    type = models.CharField(max_length=20, choices=SIGNAL_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'signals'
        ordering = ['-created_at']
        unique_together = ('investor', 'founder')  # One signal per investor-founder pair
        indexes = [
            models.Index(fields=['investor', 'founder']),
            models.Index(fields=['founder', 'type']),
            models.Index(fields=['investor', 'type']),
        ]

    def __str__(self):
        return f"{self.investor.name} -> {self.founder.name}: {self.type}"