import json
import jwt
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.conf import settings
from .models import ChatRoom, Message

User = get_user_model()

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        """Handle WebSocket connection"""
        self.chat_room_id = self.scope['url_route']['kwargs']['chat_room_id']
        self.room_group_name = f'chat_{self.chat_room_id}'
        
        # Get user from JWT token
        self.user = await self.get_user_from_token()
        
        if not self.user:
            await self.close(code=4001)  # Unauthorized
            return
        
        # Check if user is participant in this chat room
        is_participant = await self.check_user_participation()
        if not is_participant:
            await self.close(code=4003)  # Forbidden
            return
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Notify that user joined
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_joined',
                'user_id': self.user.id,
                'username': self.user.username
            }
        )

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        if hasattr(self, 'user') and self.user:
            # Notify that user left
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'user_left',
                    'user_id': self.user.id,
                    'username': self.user.username
                }
            )
        
        # Leave room group
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

    async def receive(self, text_data):
        """Handle incoming WebSocket messages"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type', 'message')
            
            if message_type == 'typing':
                # Handle typing indicator
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'typing_indicator',
                        'user_id': self.user.id,
                        'username': self.user.username,
                        'is_typing': data.get('is_typing', False)
                    }
                )
            
            elif message_type == 'message':
                # Handle chat message
                content = data.get('content', '').strip()
                if content:
                    # Save message to database
                    message = await self.save_message(content)
                    if message:
                        # Send message to room group
                        await self.channel_layer.group_send(
                            self.room_group_name,
                            {
                                'type': 'chat_message',
                                'message': await self.serialize_message(message)
                            }
                        )
            
            elif message_type == 'mark_read':
                # Handle marking messages as read
                message_id = data.get('message_id')
                if message_id:
                    await self.mark_message_read(message_id)
        
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'error': 'Invalid JSON'
            }))
        except Exception as e:
            await self.send(text_data=json.dumps({
                'error': str(e)
            }))

    async def chat_message(self, event):
        """Send chat message to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message': event['message']
        }))

    async def typing_indicator(self, event):
        """Send typing indicator to WebSocket"""
        # Don't send typing indicator back to the sender
        if event['user_id'] != self.user.id:
            await self.send(text_data=json.dumps({
                'type': 'typing_indicator',
                'user_id': event['user_id'],
                'username': event['username'],
                'is_typing': event['is_typing']
            }))

    async def user_joined(self, event):
        """Send user joined notification to WebSocket"""
        if event['user_id'] != self.user.id:
            await self.send(text_data=json.dumps({
                'type': 'user_joined',
                'user_id': event['user_id'],
                'username': event['username']
            }))

    async def user_left(self, event):
        """Send user left notification to WebSocket"""
        if event['user_id'] != self.user.id:
            await self.send(text_data=json.dumps({
                'type': 'user_left',
                'user_id': event['user_id'],
                'username': event['username']
            }))

    @database_sync_to_async
    def get_user_from_token(self):
        """Extract user from JWT token in query parameters"""
        try:
            token = None
            query_string = self.scope.get('query_string', b'').decode()
            
            # Parse query string to get token
            for param in query_string.split('&'):
                if param.startswith('token='):
                    token = param.split('=')[1]
                    break
            
            if not token:
                return None
            
            # Decode JWT token
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
            user_id = payload.get('user_id')
            
            if user_id:
                return User.objects.get(id=user_id)
            
        except (jwt.InvalidTokenError, User.DoesNotExist, Exception):
            pass
        
        return None

    @database_sync_to_async
    def check_user_participation(self):
        """Check if user is a participant in the chat room"""
        try:
            chat_room = ChatRoom.objects.get(id=self.chat_room_id)
            return chat_room.participants.filter(id=self.user.id).exists()
        except ChatRoom.DoesNotExist:
            return False

    @database_sync_to_async
    def save_message(self, content):
        """Save message to database"""
        try:
            chat_room = ChatRoom.objects.get(id=self.chat_room_id)
            message = Message.objects.create(
                chat_room=chat_room,
                sender=self.user,
                content=content,
                message_type='text'
            )
            
            # Update chat room timestamp
            chat_room.save(update_fields=['updated_at'])
            
            return message
        except Exception:
            return None

    @database_sync_to_async
    def serialize_message(self, message):
        """Serialize message for WebSocket transmission"""
        return {
            'id': message.id,
            'content': message.content,
            'message_type': message.message_type,
            'sender': {
                'id': message.sender.id,
                'username': message.sender.username,
                'first_name': message.sender.first_name,
                'last_name': message.sender.last_name,
            },
            'chat_room': message.chat_room.id,
            'created_at': message.created_at.isoformat(),
            'is_read': False,
            'read_by': []
        }

    @database_sync_to_async
    def mark_message_read(self, message_id):
        """Mark a message as read by the current user"""
        try:
            message = Message.objects.get(
                id=message_id,
                chat_room_id=self.chat_room_id
            )
            message.mark_as_read(self.user)
        except Message.DoesNotExist:
            pass