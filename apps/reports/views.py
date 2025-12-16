from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from .models import Report
from .serializers import ReportSerializer, ReportDetailSerializer


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_report_view(request):
    """Create a new report"""
    data = request.data.copy()
    data['reporter'] = request.user.id

    # Validate that either video or user is reported
    if not data.get('video') and not data.get('reported_user'):
        return Response(
            {'message': 'Either video or reported_user must be provided'},
            status=status.HTTP_400_BAD_REQUEST
        )

    serializer = ReportSerializer(data=data)
    if serializer.is_valid():
        report = serializer.save(reporter=request.user)
        return Response(ReportSerializer(report).data, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_reports_view(request):
    """Get current user's reports"""
    reports = Report.objects.filter(reporter=request.user).order_by('-created_at')
    serializer = ReportSerializer(reports, many=True)
    return Response(serializer.data)