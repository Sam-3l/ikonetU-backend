from django.urls import path
from . import views

urlpatterns = [
    # Profile management
    path('founder/profile', views.founder_profile_view, name='founder-profile'),
    path('investor/profile', views.investor_profile_view, name='investor-profile'),
    
    # Avatar upload
    path('avatar/upload', views.upload_avatar, name='upload-avatar'),
    
    # Stats
    path('stats', views.profile_stats_view, name='profile-stats'),
]