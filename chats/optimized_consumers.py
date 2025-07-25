# Enhanced Chat Consumer for Better Scalability
import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from django.core.cache import cache
from django.db import transaction
from .models import ChatRoom, Message
from .serializers import MessageSerializer

class OptimizedChatConsumer(AsyncWebsocketConsumer):
    """
    Enhanced WebSocket consumer with scalability optimizations:
    - Async database operations
    - Connection pooling
    - Rate limiting
    - Message batching
    - Memory optimization
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.room_id = None
        self.room_group_name = None
        self.user = None
        self.message_buffer = []
        self.last_flush = None
        
    async def connect(self):
        # Rate limiting check
        if not await self.check_rate_limit():
            await self.close(code=4008)  # Rate limited
            return
            
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'chat_{self.room_id}'
        self.user = self.scope["user"]
        
        if isinstance(self.user, AnonymousUser):
            await self.close(code=4001)  # Unauthorized
            return
            
        # Check room access with caching
        if not await self.check_room_access():
            await self.close(code=4003)  # Forbidden
            return
            
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()
        
        # Update user presence
        await self.update_user_presence(True)
        
        # Notify others user joined
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_presence',
                'user_id': self.user.id,
                'username': self.user.username,
                'online': True
            }
        )
    
    async def disconnect(self, close_code):
        if self.room_group_name:
            # Flush any pending messages
            await self.flush_message_buffer()
            
            # Update presence
            await self.update_user_presence(False)
            
            # Notify others user left
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'user_presence',
                    'user_id': self.user.id,
                    'username': self.user.username,
                    'online': False
                }
            )
            
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
    
    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            message_type = data.get('type', 'chat_message')
            
            if message_type == 'chat_message':
                await self.handle_chat_message(data)
            elif message_type == 'typing':
                await self.handle_typing(data)
            elif message_type == 'mark_read':
                await self.handle_mark_read(data)
                
        except json.JSONDecodeError:
            await self.send_error("Invalid JSON format")
        except Exception as e:
            await self.send_error(f"Error processing message: {str(e)}")
    
    async def handle_chat_message(self, data):
        content = data.get('content', '').strip()
        file_url = data.get('file_url')
        
        if not content and not file_url:
            await self.send_error("Message content or file required")
            return
            
        # Add to buffer for batching
        message_data = {
            'content': content,
            'file_url': file_url,
            'sender': self.user,
            'room_id': self.room_id,
            'timestamp': asyncio.get_event_loop().time()
        }
        
        self.message_buffer.append(message_data)
        
        # Flush buffer if it's getting full or enough time has passed
        if len(self.message_buffer) >= 10 or await self.should_flush_buffer():
            await self.flush_message_buffer()
        else:
            # Send immediately for real-time feel
            await self.send_message_to_group(message_data)
    
    async def flush_message_buffer(self):
        """Batch process messages for better database performance"""
        if not self.message_buffer:
            return
            
        try:
            # Bulk create messages
            messages_to_create = []
            for msg_data in self.message_buffer:
                room = await self.get_room_cached()
                message = Message(
                    room=room,
                    sender=msg_data['sender'],
                    content=msg_data['content'],
                    file_url=msg_data['file_url']
                )
                messages_to_create.append(message)
            
            # Bulk create in database
            created_messages = await database_sync_to_async(
                Message.objects.bulk_create
            )(messages_to_create)
            
            # Update cache
            await self.update_room_cache()
            
            self.message_buffer.clear()
            self.last_flush = asyncio.get_event_loop().time()
            
        except Exception as e:
            print(f"Error flushing message buffer: {e}")
    
    async def should_flush_buffer(self):
        """Check if enough time has passed to flush buffer"""
        if not self.last_flush:
            return True
        current_time = asyncio.get_event_loop().time()
        return (current_time - self.last_flush) > 5  # 5 seconds
    
    async def send_message_to_group(self, message_data):
        """Send message to WebSocket group"""
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'content': message_data['content'],
                'file_url': message_data['file_url'],
                'sender_id': message_data['sender'].id,
                'sender_username': message_data['sender'].username,
                'timestamp': message_data['timestamp']
            }
        )
    
    async def chat_message(self, event):
        """Handle incoming chat message from group"""
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'content': event['content'],
            'file_url': event['file_url'],
            'sender_id': event['sender_id'],
            'sender_username': event['sender_username'],
            'timestamp': event['timestamp']
        }))
    
    async def handle_typing(self, data):
        """Handle typing indicators"""
        is_typing = data.get('is_typing', False)
        
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'typing_indicator',
                'user_id': self.user.id,
                'username': self.user.username,
                'is_typing': is_typing
            }
        )
    
    async def typing_indicator(self, event):
        """Handle typing indicator from group"""
        if event['user_id'] != self.user.id:  # Don't send to self
            await self.send(text_data=json.dumps({
                'type': 'typing_indicator',
                'user_id': event['user_id'],
                'username': event['username'],
                'is_typing': event['is_typing']
            }))
    
    async def user_presence(self, event):
        """Handle user presence updates"""
        if event['user_id'] != self.user.id:  # Don't send to self
            await self.send(text_data=json.dumps({
                'type': 'user_presence',
                'user_id': event['user_id'],
                'username': event['username'],
                'online': event['online']
            }))
    
    async def check_rate_limit(self):
        """Check rate limiting per user"""
        cache_key = f"chat_rate_limit_{self.scope['client'][0]}"
        current_count = cache.get(cache_key, 0)
        
        if current_count > 100:  # Max 100 connections per minute per IP
            return False
            
        cache.set(cache_key, current_count + 1, 60)
        return True
    
    @database_sync_to_async
    def check_room_access(self):
        """Check if user has access to chat room with caching"""
        cache_key = f"room_access_{self.room_id}_{self.user.id}"
        cached_result = cache.get(cache_key)
        
        if cached_result is not None:
            return cached_result
            
        try:
            room = ChatRoom.objects.get(id=self.room_id)
            has_access = room.participants.filter(id=self.user.id).exists()
            cache.set(cache_key, has_access, 300)  # Cache for 5 minutes
            return has_access
        except ChatRoom.DoesNotExist:
            return False
    
    @database_sync_to_async
    def get_room_cached(self):
        """Get room with caching"""
        cache_key = f"chat_room_{self.room_id}"
        cached_room = cache.get(cache_key)
        
        if cached_room:
            return cached_room
            
        room = ChatRoom.objects.get(id=self.room_id)
        cache.set(cache_key, room, 300)
        return room
    
    async def update_room_cache(self):
        """Update room cache after changes"""
        cache_key = f"chat_room_{self.room_id}"
        cache.delete(cache_key)
    
    async def update_user_presence(self, online=True):
        """Update user presence in cache"""
        cache_key = f"user_presence_{self.user.id}"
        cache.set(cache_key, online, 300)
    
    async def send_error(self, message):
        """Send error message to client"""
        await self.send(text_data=json.dumps({
            'type': 'error',
            'message': message
        }))
