from django.urls import path
from apps.profiles import views

urlpatterns = [
    path('profile', views.investor_profile_view, name='investor-profile'),
    path('profile/<uuid:user_id>', views.investor_profile_detail_view, name='investor-profile-detail'),
]