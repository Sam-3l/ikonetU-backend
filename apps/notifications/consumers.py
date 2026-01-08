from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async


class NotificationConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        if self.scope['user'].is_authenticated:
            self.user_id = str(self.scope['user'].id)
            self.group_name = f"user_{self.user_id}"
            
            await self.channel_layer.group_add(
                self.group_name,
                self.channel_name
            )
            
            await self.accept()
        else:
            await self.close()
    
    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )
    
    async def notification_message(self, event):
        """Receive notification from channel layer and send to WebSocket"""
        await self.send_json({
            'type': 'notification',
            'notification': event['notification']
        })