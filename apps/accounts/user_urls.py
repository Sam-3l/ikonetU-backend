from django.urls import path
from . import user_views
from . import views

urlpatterns = [
    path('onboarding-complete', user_views.onboarding_complete_view, name='onboarding-complete'),
    path('<uuid:user_id>/profile', views.get_user_profile, name='user-profile-detail'),
]