from django.urls import path
from . import views

urlpatterns = [
    path('feed/', views.video_feed_view, name='video-feed'),
    path('my/', views.my_videos_view, name='my-videos'),
    path('', views.create_video_view, name='create-video'),
    path('<uuid:video_id>/', views.video_detail_and_update_view, name='video-detail'),
]