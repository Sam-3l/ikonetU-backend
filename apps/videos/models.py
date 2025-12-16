import uuid
from django.db import models
from apps.accounts.models import User


class Video(models.Model):
    STATUS_CHOICES = [
        ('processing', 'Processing'),   # Current - awaiting approval
        ('active', 'Active'),            # Current - approved
        ('rejected', 'Rejected'),        # Current - rejected by admin
        ('archived', 'Archived'),        # Not current - old video
        ('deleted', 'Deleted'),          # Not current - soft deleted
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    founder = models.ForeignKey(User, on_delete=models.CASCADE, related_name='videos')
    url = models.URLField(max_length=500)
    thumbnail_url = models.URLField(max_length=500, blank=True, default='')
    title = models.CharField(max_length=255, blank=True, default='')
    duration = models.FloatField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='processing')
    view_count = models.IntegerField(default=0)
    is_current = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'videos'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['founder', 'is_current', 'status']),
        ]

    def __str__(self):
        return f"{self.founder.name} - {self.title or 'Untitled'} ({'Current' if self.is_current else 'History'})"

    def save(self, *args, **kwargs):
        # When setting a video as current, archive ONLY the previous current video
        if self.is_current:
            Video.objects.filter(
                founder=self.founder,
                is_current=True,
                status__in=['processing', 'active', 'rejected']  # Only archive previous current videos
            ).exclude(id=self.id).update(
                is_current=False,
                status='archived'
            )
        super().save(*args, **kwargs)