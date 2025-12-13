from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import LegalConsent
from .serializers import LegalConsentSerializer


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def legal_consent_view(request):
    """Get or create user's legal consent"""
    
    if request.method == 'GET':
        try:
            consent = LegalConsent.objects.get(user=request.user)
            serializer = LegalConsentSerializer(consent)
            return Response(serializer.data)
        except LegalConsent.DoesNotExist:
            return Response(None, status=status.HTTP_200_OK)
    
    elif request.method == 'POST':
        # Check if consent already exists
        consent, created = LegalConsent.objects.get_or_create(
            user=request.user,
            defaults={
                'accepted_terms': request.data.get('acceptedTerms', False),
                'accepted_nda': request.data.get('acceptedNda', False),
                'ip_address': request.META.get('REMOTE_ADDR'),
            }
        )
        
        if not created:
            # Update existing consent
            consent.accepted_terms = request.data.get('acceptedTerms', consent.accepted_terms)
            consent.accepted_nda = request.data.get('acceptedNda', consent.accepted_nda)
            consent.save()
        
        serializer = LegalConsentSerializer(consent)
        return Response(serializer.data, status=status.HTTP_201_CREATED)