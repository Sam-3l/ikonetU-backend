from rest_framework import serializers
from .models import LegalConsent


class LegalConsentSerializer(serializers.ModelSerializer):
    class Meta:
        model = LegalConsent
        fields = '__all__'
        read_only_fields = ['id', 'user', 'accepted_at']