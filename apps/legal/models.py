import uuid
from django.db import models
from apps.accounts.models import User


class LegalConsent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='legal_consent')
    accepted_terms = models.BooleanField(default=False)
    accepted_nda = models.BooleanField(default=False)
    accepted_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        db_table = 'legal_consent'

    def __str__(self):
        return f"{self.user.email} - Consent"