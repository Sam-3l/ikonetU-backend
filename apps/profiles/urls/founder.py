from django.urls import path
from apps.profiles import views

urlpatterns = [
    path('profile', views.founder_profile_view, name='founder-profile'),
    path('profile/<uuid:user_id>', views.founder_profile_detail_view, name='founder-profile-detail'),
]