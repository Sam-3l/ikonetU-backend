from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_stats_view(request):
    """
    Get dashboard statistics based on user role
    TODO: Implement after models are created
    """
    user = request.user
    
    if user.role == 'founder':
        # TODO: Get founder statistics
        return Response({
            'totalViews': 0,
            'interestedCount': 0,
            'maybeCount': 0,
            'activeMatches': 0,
            'pendingMatches': 0,
            'videoCount': 0,
        })
    
    elif user.role == 'investor':
        # TODO: Get investor statistics
        return Response({
            'signalsSent': 0,
            'interestedCount': 0,
            'maybeCount': 0,
            'passCount': 0,
            'activeMatches': 0,
            'pendingMatches': 0,
        })
    
    elif user.role == 'admin':
        # TODO: Get admin statistics
        return Response({
            'totalUsers': 0,
            'totalFounders': 0,
            'totalInvestors': 0,
            'totalVideos': 0,
            'activeVideos': 0,
            'pendingReports': 0,
        })
    
    return Response({'message': 'Invalid role'}, status=status.HTTP_400_BAD_REQUEST)