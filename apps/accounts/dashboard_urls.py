from django.urls import path
from . import dashboard_views

urlpatterns = [
    path('stats', dashboard_views.dashboard_stats_view, name='dashboard-stats'),
]