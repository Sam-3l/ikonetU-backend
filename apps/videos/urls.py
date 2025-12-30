from django.urls import path
from . import views

urlpatterns = [
    path('feed/', views.video_feed_view, name='video-feed'),
    path('my/', views.my_videos_view, name='my-videos'),
    path('history/', views.video_history_view, name='video-history'),
    path('', views.create_video_view, name='create-video'),
    path('<uuid:video_id>/', views.video_detail_and_update_view, name='video-detail'),
    path('<uuid:video_id>/set-current/', views.set_video_as_current_view, name='set-video-current'),
    path('<uuid:video_id>/delete/', views.delete_video_view, name='delete-video'),
    path('<uuid:video_id>/like/', views.like_video_view, name='like-video'),
    path('<uuid:video_id>/track-view/', views.track_video_view, name='track-video-view'),
]