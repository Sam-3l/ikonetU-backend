import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from django.core.cache import cache
from .models import Match, Message
from apps.accounts.models import User


class ChatConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time chat
    Each match has its own room
    Presence is handled by PresenceConsumer, this only handles messages
    """

    async def connect(self):
        """Handle WebSocket connection"""
        self.match_id = self.scope['url_route']['kwargs']['match_id']
        self.room_group_name = f'chat_{self.match_id}'
        self.user = self.scope['user']

        if not self.user.is_authenticated:
            await self.close()
            return

        match_data = await self.verify_match_access()
        if not match_data:
            await self.close()
            return
        
        self.other_user_id = match_data['other_user_id']

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

        # Mark messages as delivered and broadcast status updates
        delivered_ids = await self.mark_messages_delivered()
        
        for message_id in delivered_ids:
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'message_status_update',
                    'message_id': str(message_id),
                    'status': 'delivered',
                }
            )

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
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

            message = await self.save_message(content)
            
            # Check if other user is online to determine initial status
            is_other_user_online = cache.get(f'user_online_global_{self.other_user_id}', False)
            initial_status = 'delivered' if is_other_user_online else 'sent'
            
            # Update message status if delivered
            if initial_status == 'delivered':
                await self.update_message_status(str(message.id), 'delivered')

            # Broadcast to chat room
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': {
                        'id': str(message.id),
                        'sender_id': str(message.sender.id),
                        'content': message.content,
                        'status': initial_status,
                        'created_at': message.created_at.isoformat(),
                    }
                }
            )

            # ALSO broadcast to global presence for unread notifications
            await self.channel_layer.group_send(
                f'match_presence_{str(self.match_id)}',
                {
                    'type': 'new_message_notification',
                    'match_id': str(self.match_id),
                    'message_id': str(message.id),
                    'sender_id': str(self.user.id),
                }
            )

        elif message_type == 'message_read':
            message_id = data.get('message_id')
            await self.mark_message_read(message_id)

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'message_status_update',
                    'message_id': message_id,
                    'status': 'read',
                }
            )

        elif message_type == 'typing':
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'typing_indicator',
                    'user_id': str(self.user.id),
                    'is_typing': data.get('is_typing', False),
                }
            )
        
        elif message_type == 'mark_read':
            read_ids = await self.mark_all_messages_read()
            for message_id in read_ids:
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'message_status_update',
                        'message_id': str(message_id),
                        'status': 'read',
                    }
                )
        
        elif message_type == 'ping':
            await self.send(text_data=json.dumps({
                'type': 'pong'
            }))

    async def chat_message(self, event):
        """Send chat message to WebSocket"""
        message = event['message']

        if 'created_at' in message:
            if not isinstance(message['created_at'], str):
                message['created_at'] = message['created_at'].isoformat()

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
        if event['user_id'] != str(self.user.id):
            await self.send(text_data=json.dumps({
                'type': 'typing_indicator',
                'user_id': event['user_id'],
                'is_typing': event['is_typing'],
            }))

    @database_sync_to_async
    def verify_match_access(self):
        """Verify user has access to this match and return other user's ID"""
        try:
            match = Match.objects.get(
                id=self.match_id,
                is_active=True
            )
            is_investor = match.investor_id == self.user.id
            is_founder = match.founder_id == self.user.id
            
            if not (is_investor or is_founder):
                return None
            
            other_user_id = match.founder_id if is_investor else match.investor_id
            
            return {
                'valid': True,
                'other_user_id': other_user_id
            }
        except Match.DoesNotExist:
            return None

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
        """Mark all undelivered messages as delivered and return their IDs"""
        messages = Message.objects.filter(
            match_id=self.match_id,
            status='sent'
        ).exclude(sender=self.user)
        
        message_ids = list(messages.values_list('id', flat=True))
        
        messages.update(
            status='delivered',
            delivered_at=timezone.now()
        )
        
        return message_ids

    @database_sync_to_async
    def mark_message_delivered_by_id(self, message_id):
        """Mark specific message as delivered"""
        try:
            Message.objects.filter(
                id=message_id,
                status='sent'
            ).exclude(sender=self.user).update(
                status='delivered',
                delivered_at=timezone.now()
            )
        except Exception:
            pass

    @database_sync_to_async
    def mark_message_read(self, message_id):
        """Mark message as read"""
        try:
            message = Message.objects.get(id=message_id)
            if message.sender_id != self.user.id:
                message.status = 'read'
                message.read_at = timezone.now()
                message.save(update_fields=['status', 'read_at'])
        except Message.DoesNotExist:
            pass

    @database_sync_to_async
    def mark_all_messages_read(self):
        """Mark all messages from other user as read and return their IDs"""
        messages = Message.objects.filter(
            match_id=self.match_id,
            status__in=['sent', 'delivered']
        ).exclude(sender=self.user)
        
        message_ids = list(messages.values_list('id', flat=True))
        
        messages.update(
            status='read',
            read_at=timezone.now()
        )
        
        return message_ids

    @database_sync_to_async
    def update_message_status(self, message_id, status):
        """Update message status"""
        try:
            message = Message.objects.get(id=message_id)
            message.status = status
            if status == 'delivered':
                message.delivered_at = timezone.now()
            elif status == 'read':
                message.read_at = timezone.now()
            message.save()
        except Message.DoesNotExist:
            pass


class PresenceConsumer(AsyncWebsocketConsumer):
    """
    Global presence WebSocket consumer
    SINGLE SOURCE OF TRUTH for online/offline status
    ALSO handles real-time new message notifications
    """

    async def connect(self):
        """Handle WebSocket connection"""
        self.user = self.scope['user']

        if not self.user.is_authenticated:
            await self.close()
            return

        self.user_id = str(self.user.id)
        self.presence_group = f'user_presence_{self.user_id}'

        await self.channel_layer.group_add(
            self.presence_group,
            self.channel_name
        )

        await self.accept()

        # Set global online status (no timeout - must be explicitly cleared)
        cache.set(f'user_online_global_{self.user_id}', True, timeout=None)

        match_ids = await self.get_user_matches()

        # Join presence groups for all matches
        for match_id in match_ids:
            await self.channel_layer.group_add(
                f'match_presence_{match_id}',
                self.channel_name
            )

        # Broadcast online status
        for match_id in match_ids:
            await self.channel_layer.group_send(
                f'match_presence_{match_id}',
                {
                    'type': 'user_status_update',
                    'user_id': self.user_id,
                    'is_online': True,
                }
            )

        # Mark all undelivered messages to this user as delivered
        delivered_message_ids = await self.mark_all_undelivered_messages()
        
        # Broadcast delivery status to both chat rooms AND presence groups
        for match_id, message_ids in delivered_message_ids.items():
            for message_id in message_ids:
                # Broadcast to chat room (for users currently in the chat)
                await self.channel_layer.group_send(
                    f'chat_{match_id}',
                    {
                        'type': 'message_status_update',
                        'message_id': str(message_id),
                        'status': 'delivered',
                    }
                )
                # ALSO broadcast to presence group (for all users in the match)
                await self.channel_layer.group_send(
                    f'match_presence_{match_id}',
                    {
                        'type': 'message_status_broadcast',
                        'message_id': str(message_id),
                        'status': 'delivered',
                    }
                )

        await self.send_initial_statuses(match_ids)

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        user_id = getattr(self, "user_id", None)
        presence_group = getattr(self, "presence_group", None)

        if not user_id:
            return

        # Clear global online status
        cache.delete(f'user_online_global_{user_id}')

        match_ids = await self.get_user_matches()

        # Broadcast offline
        for match_id in match_ids:
            await self.channel_layer.group_send(
                f'match_presence_{match_id}',
                {
                    'type': 'user_status_update',
                    'user_id': user_id,
                    'is_online': False,
                    'is_typing': False,
                }
            )

        if presence_group:
            await self.channel_layer.group_discard(
                presence_group,
                self.channel_name
            )

        for match_id in match_ids:
            await self.channel_layer.group_discard(
                f'match_presence_{match_id}',
                self.channel_name
            )

    async def receive(self, text_data):
        """Receive message from WebSocket"""
        data = json.loads(text_data)
        message_type = data.get('type')

        if message_type == 'typing':
            match_id = data.get('match_id')
            is_typing = data.get('is_typing', False)

            if match_id:
                # Broadcast typing to global presence listeners
                await self.channel_layer.group_send(
                    f'match_presence_{match_id}',
                    {
                        'type': 'typing_status_update',
                        'user_id': self.user_id,
                        'match_id': match_id,
                        'is_typing': is_typing,
                    }
                )

        elif message_type == 'ping':
            await self.send(text_data=json.dumps({
                'type': 'pong'
            }))

    async def user_status_update(self, event):
        """Send user online/offline status update"""
        if event['user_id'] != self.user_id:
            await self.send(text_data=json.dumps({
                'type': 'user_status',
                'user_id': event['user_id'],
                'is_online': event['is_online'],
                'is_typing': event.get('is_typing', False),
            }))

    async def typing_status_update(self, event):
        """Send typing indicator update"""
        if event['user_id'] != self.user_id:
            await self.send(text_data=json.dumps({
                'type': 'typing_status',
                'user_id': event['user_id'],
                'match_id': event['match_id'],
                'is_typing': event['is_typing'],
            }))

    async def new_message_notification(self, event):
        """Send new message notification for real-time unread updates"""
        # Only notify if it's not your own message
        if event['sender_id'] != self.user_id:
            await self.send(text_data=json.dumps({
                'type': 'new_message',
                'match_id': event['match_id'],
                'message_id': event['message_id'],
                'sender_id': event['sender_id'],
            }))

    async def message_status_broadcast(self, event):
        """Broadcast message status updates (delivered/read) via global presence"""
        await self.send(text_data=json.dumps({
            'type': 'message_status_update',
            'message_id': event['message_id'],
            'status': event['status'],
        }))

    async def send_initial_statuses(self, match_ids):
        """Send initial online status of all matched users"""
        other_user_ids = await self.get_other_users_from_matches(match_ids)
        
        statuses = {}
        for user_id in other_user_ids:
            is_online = cache.get(f'user_online_global_{user_id}', False)
            statuses[user_id] = is_online

        await self.send(text_data=json.dumps({
            'type': 'initial_statuses',
            'statuses': statuses
        }))

    async def match_status_update(self, event):
        """Send match status update notification"""
        await self.send(text_data=json.dumps({
            'type': 'match_status_update',
            'match_id': event['match_id'],
            'is_active': event['is_active'],
        }))

    @database_sync_to_async
    def get_user_matches(self):
        """Get all match IDs for the current user"""
        from apps.matches.models import Match
        
        matches = Match.objects.filter(
            is_active=True
        ).filter(
            investor_id=self.user.id
        ) | Match.objects.filter(
            is_active=True,
            founder_id=self.user.id
        )
        
        return [str(m.id) for m in matches]

    @database_sync_to_async
    def get_other_users_from_matches(self, match_ids):
        """Get all other user IDs from matches"""
        from apps.matches.models import Match
        
        matches = Match.objects.filter(id__in=match_ids)
        other_user_ids = []
        
        for match in matches:
            if str(match.investor_id) == self.user_id:
                other_user_ids.append(str(match.founder_id))
            else:
                other_user_ids.append(str(match.investor_id))
        
        return other_user_ids

    @database_sync_to_async
    def mark_all_undelivered_messages(self):
        """Mark all undelivered messages to this user as delivered across all matches"""
        from apps.matches.models import Match, Message
        
        # Get all matches for this user
        matches = Match.objects.filter(
            is_active=True
        ).filter(
            investor_id=self.user.id
        ) | Match.objects.filter(
            is_active=True,
            founder_id=self.user.id
        )
        
        result = {}
        
        for match in matches:
            # Get all 'sent' messages in this match that are NOT from this user
            messages = Message.objects.filter(
                match_id=match.id,
                status='sent'
            ).exclude(sender_id=self.user.id)
            
            message_ids = list(messages.values_list('id', flat=True))
            
            if message_ids:
                # Update to delivered
                messages.update(
                    status='delivered',
                    delivered_at=timezone.now()
                )
                result[str(match.id)] = message_ids
        
        return result