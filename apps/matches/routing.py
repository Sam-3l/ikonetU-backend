from django.urls import path
from . import consumers
from .middleware import TokenAuthMiddleware

websocket_urlpatterns = [
    path('ws/chat/<uuid:match_id>/', TokenAuthMiddleware(consumers.ChatConsumer.as_asgi())),
    path('ws/presence/', TokenAuthMiddleware(consumers.PresenceConsumer.as_asgi())),
]