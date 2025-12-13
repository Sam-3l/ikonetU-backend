from django.urls import path
from . import user_views

urlpatterns = [
    path('onboarding-complete', user_views.onboarding_complete_view, name='onboarding-complete'),
]