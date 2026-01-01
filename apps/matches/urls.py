from django.urls import path
from . import views, message_views

urlpatterns = [
    # Matches
    path('', views.my_matches_view, name='my-matches'),
    path('<uuid:match_id>/', views.match_detail_view, name='match-detail'),
    path('<uuid:match_id>/unmatch/', views.unmatch_view, name='unmatch'),
    path('<uuid:match_id>/accept/', views.accept_match_view, name='accept-match'),
    path('<uuid:match_id>/reject/', views.reject_match_view, name='reject-match'),
    
    # Messages
    path('<uuid:match_id>/messages/', message_views.match_messages_view, name='match-messages'),
    path('<uuid:match_id>/messages/send/', message_views.send_message_view, name='send-message'),
    path('<uuid:match_id>/messages/mark-delivered/', message_views.mark_messages_delivered_view),
    path('<uuid:match_id>/messages/mark-read/', message_views.mark_messages_read_view, name='mark-messages-read'),
    path('unread-count/', message_views.unread_count_view, name='unread-count'),
]