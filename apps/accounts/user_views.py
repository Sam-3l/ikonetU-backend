from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def onboarding_complete_view(request):
    """
    Mark user onboarding as complete
    """
    user = request.user
    user.onboarding_complete = True
    user.save()
    
    return Response({'success': True})