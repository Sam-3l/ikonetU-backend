from django.urls import path
from . import views

urlpatterns = [
    path('consent', views.legal_consent_view, name='legal-consent'),
]