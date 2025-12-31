import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from .models import Match, Message
from apps.accounts.models import User


class ChatConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time chat
    Each match has its own room
    """

    async def connect(self):
        """Handle WebSocket connection"""
        self.match_id = self.scope['url_route']['kwargs']['match_id']
        self.room_group_name = f'chat_{self.match_id}'
        self.user = self.scope['user']

        # Verify user is authenticated
        if not self.user.is_authenticated:
            await self.close()
            return

        # Verify user is part of this match
        is_valid = await self.verify_match_access()
        if not is_valid:
            await self.close()
            return

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

        # Mark all messages as delivered when user connects
        await self.mark_messages_delivered()

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        """Receive message from WebSocket"""
        data = json.loads(text_data)
        message_type = data.get('type')

        if message_type == 'chat_message':
            content = data.get('content', '').strip()
            
            if not content or len(content) > 5000:
                return

            # Save message to database
            message = await self.save_message(content)

            # Send message to room group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': {
                        'id': str(message.id),
                        'sender_id': str(message.sender.id),
                        'content': message.content,
                        'status': message.status,
                        'created_at': message.created_at.isoformat(),
                    }
                }
            )

        elif message_type == 'message_read':
            message_id = data.get('message_id')
            await self.mark_message_read(message_id)

            # Notify sender that message was read
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'message_status_update',
                    'message_id': message_id,
                    'status': 'read',
                }
            )

        elif message_type == 'typing':
            # Broadcast typing indicator
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'typing_indicator',
                    'user_id': str(self.user.id),
                    'is_typing': data.get('is_typing', False),
                }
            )

    async def chat_message(self, event):
        """Send chat message to WebSocket"""
        message = event['message']
        
        # Mark as delivered if this is the recipient
        if message['sender_id'] != str(self.user.id):
            await self.mark_message_delivered_by_id(message['id'])
            message['status'] = 'delivered'

        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message': message
        }))

    async def message_status_update(self, event):
        """Send message status update to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'message_status_update',
            'message_id': event['message_id'],
            'status': event['status'],
        }))

    async def typing_indicator(self, event):
        """Send typing indicator to WebSocket"""
        # Don't send to the user who is typing
        if event['user_id'] != str(self.user.id):
            await self.send(text_data=json.dumps({
                'type': 'typing_indicator',
                'user_id': event['user_id'],
                'is_typing': event['is_typing'],
            }))

    @database_sync_to_async
    def verify_match_access(self):
        """Verify user has access to this match"""
        try:
            match = Match.objects.get(
                id=self.match_id,
                is_active=True
            )
            return match.investor_id == self.user.id or match.founder_id == self.user.id
        except Match.DoesNotExist:
            return False

    @database_sync_to_async
    def save_message(self, content):
        """Save message to database"""
        match = Match.objects.get(id=self.match_id)
        message = Message.objects.create(
            match=match,
            sender=self.user,
            content=content,
            status='sent'
        )
        return message

    @database_sync_to_async
    def mark_messages_delivered(self):
        """Mark all undelivered messages as delivered"""
        Message.objects.filter(
            match_id=self.match_id,
            status='sent'
        ).exclude(sender=self.user).update(
            status='delivered',
            delivered_at=timezone.now()
        )

    @database_sync_to_async
    def mark_message_delivered_by_id(self, message_id):
        """Mark specific message as delivered"""
        try:
            message = Message.objects.get(id=message_id)
            if message.status == 'sent' and message.sender_id != self.user.id:
                message.mark_delivered()
        except Message.DoesNotExist:
            pass

    @database_sync_to_async
    def mark_message_read(self, message_id):
        """Mark message as read"""
        try:
            message = Message.objects.get(id=message_id)
            if message.sender_id != self.user.id:
                message.mark_read()
        except Message.DoesNotExist:
            pass