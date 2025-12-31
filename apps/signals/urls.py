from django.urls import path
from . import views

urlpatterns = [
    path('', views.create_signal_view, name='create-signal'),
    path('my/', views.my_signals_view, name='my-signals'),
    path('received/', views.signals_received_view, name='signals-received'),
]