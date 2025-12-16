from django.urls import path
from . import admin_views

urlpatterns = [
    path('reports/', admin_views.admin_reports_view, name='admin-reports'),
    path('reports/<uuid:report_id>/', admin_views.admin_update_report_view, name='admin-update-report'),
    path('reports/<uuid:report_id>/delete/', admin_views.admin_delete_report_view, name='admin-delete-report'),
]