import uuid
from django.db import models
from apps.accounts.models import User


class Video(models.Model):
    STATUS_CHOICES = [
        ('processing', 'Processing'),
        ('active', 'Active'),
        ('rejected', 'Rejected'),
        ('archived', 'Archived'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    founder = models.ForeignKey(User, on_delete=models.CASCADE, related_name='videos')
    url = models.URLField(max_length=500)
    thumbnail_url = models.URLField(max_length=500, blank=True, default='')
    title = models.CharField(max_length=255, blank=True, default='')
    duration = models.IntegerField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='processing')
    view_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'videos'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.founder.name} - {self.title or 'Untitled'}"