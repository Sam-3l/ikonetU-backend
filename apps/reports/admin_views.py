from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from .models import Report
from .serializers import ReportDetailSerializer


def require_admin(view_func):
    """Decorator to check if user is admin"""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response({'message': 'Unauthorized'}, status=status.HTTP_401_UNAUTHORIZED)
        if request.user.role != 'admin':
            return Response({'message': 'Admin access required'}, status=status.HTTP_403_FORBIDDEN)
        return view_func(request, *args, **kwargs)
    return wrapper


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@require_admin
def admin_reports_view(request):
    """Get all reports (optionally filtered by status)"""
    status_filter = request.GET.get('status', None)
    
    reports = Report.objects.select_related('reporter', 'video', 'reported_user', 'resolved_by').order_by('-created_at')
    
    if status_filter:
        reports = reports.filter(status=status_filter)
    
    serializer = ReportDetailSerializer(reports, many=True)
    return Response(serializer.data)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
@require_admin
def admin_update_report_view(request, report_id):
    """Update report status (resolve, dismiss, etc.)"""
    try:
        report = Report.objects.get(id=report_id)
        new_status = request.data.get('status')
        
        if new_status not in ['pending', 'reviewed', 'resolved', 'dismissed']:
            return Response(
                {'message': 'Invalid status'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        report.status = new_status
        
        # Mark as resolved if status is resolved or dismissed
        if new_status in ['resolved', 'dismissed']:
            report.resolved_by = request.user
            report.resolved_at = timezone.now()
        
        report.save()
        
        return Response(ReportDetailSerializer(report).data)
        
    except Report.DoesNotExist:
        return Response({'message': 'Report not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
@require_admin
def admin_delete_report_view(request, report_id):
    """Delete a report permanently"""
    try:
        report = Report.objects.get(id=report_id)
        report.delete()
        return Response({'message': 'Report deleted successfully'})
    except Report.DoesNotExist:
        return Response({'message': 'Report not found'}, status=status.HTTP_404_NOT_FOUND)