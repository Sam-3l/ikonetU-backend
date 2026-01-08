from django.urls import path
from . import views

urlpatterns = [
    path('', views.notifications_list_view, name='notifications-list'),
    path('unread-count/', views.unread_count_view, name='unread-count'),
    path('<uuid:notification_id>/read/', views.mark_notification_read_view, name='mark-read'),
    path('mark-all-read/', views.mark_all_read_view, name='mark-all-read'),
    path('<uuid:notification_id>/delete/', views.delete_notification_view, name='delete-notification'),
    path('clear-all/', views.clear_all_notifications_view, name='clear-all'),
]