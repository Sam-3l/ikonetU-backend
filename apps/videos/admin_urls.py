from django.urls import path
from . import admin_views

urlpatterns = [
    path('stats/', admin_views.admin_dashboard_stats_view, name='admin-stats'),
    path('users/', admin_views.admin_users_view, name='admin-users'),
    path('videos/', admin_views.admin_videos_view, name='admin-videos'),
    path('videos/<uuid:video_id>/approve/', admin_views.admin_approve_video_view, name='admin-approve-video'),
    path('videos/<uuid:video_id>/reject/', admin_views.admin_reject_video_view, name='admin-reject-video'),
    path('users/<uuid:user_id>/delete/', admin_views.admin_delete_user_view, name='admin-delete-user'),
]