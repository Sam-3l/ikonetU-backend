from django.urls import path
from . import views

urlpatterns = [
    path('', views.create_report_view, name='create-report'),
    path('my/', views.my_reports_view, name='my-reports'),
]