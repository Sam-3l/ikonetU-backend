import uuid
from django.db import models
from apps.accounts.models import User


class FounderProfile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='founder_profile')
    company_name = models.CharField(max_length=255)
    location = models.CharField(max_length=255, blank=True, default='')
    bio = models.TextField(blank=True, default='')
    sector = models.CharField(max_length=100, blank=True, default='')
    stage = models.CharField(max_length=100, blank=True, default='')
    funding_goal = models.CharField(max_length=100, blank=True, default='')
    website = models.URLField(blank=True, default='')
    linkedin = models.URLField(blank=True, default='')

    class Meta:
        db_table = 'founder_profiles'

    def __str__(self):
        return f"{self.user.name} - {self.company_name}"


class InvestorProfile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='investor_profile')
    firm_name = models.CharField(max_length=255, blank=True, default='')
    title = models.CharField(max_length=255, blank=True, default='')
    thesis = models.TextField(blank=True, default='')
    sectors = models.JSONField(default=list, blank=True)
    stages = models.JSONField(default=list, blank=True)
    check_size = models.CharField(max_length=100, blank=True, default='')
    support_types = models.JSONField(default=list, blank=True)
    linkedin = models.URLField(blank=True, default='')

    class Meta:
        db_table = 'investor_profiles'

    def __str__(self):
        return f"{self.user.name} - {self.firm_name or 'Investor'}"