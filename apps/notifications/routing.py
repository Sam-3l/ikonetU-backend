from django.urls import path
from . import consumers
from apps.matches.middleware import TokenAuthMiddleware

websocket_urlpatterns = [
    path('ws/notifications/', TokenAuthMiddleware(consumers.NotificationConsumer.as_asgi())),
]