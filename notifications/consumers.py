import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
import logging

logger = logging.getLogger(__name__)

class NotificationsConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        """
        Handle WebSocket connection with JWT authentication
        """
        # Check if user is authenticated (JWT middleware handles this)
        if isinstance(self.scope['user'], AnonymousUser):
            logger.warning("WebSocket connection rejected: User not authenticated")
            await self.close()
            return
        
        self.user = self.scope['user']
        self.user_id = self.user.id
        self.group_name = f'notifications_{self.user_id}'
        
        # Join notification group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        
        logger.info(f"User {self.user.username} connected to notifications")
        await self.accept()

    async def disconnect(self, close_code):
        """
        Handle WebSocket disconnection
        """
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )
            logger.info(f"User {getattr(self, 'user', 'unknown')} disconnected from notifications")

    async def receive(self, text_data):
        """
        Handle messages from WebSocket client
        """
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'ping':
                # Respond to ping with pong
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'timestamp': data.get('timestamp')
                }))
            else:
                logger.warning(f"Unknown message type: {message_type}")
                
        except json.JSONDecodeError:
            logger.error("Invalid JSON received from WebSocket client")

    async def send_notification(self, event):
        """
        Send notification to WebSocket client
        """
        await self.send(text_data=json.dumps(event['notification']))

    async def notification_message(self, event):
        """
        Handle notification messages from channel layer
        """
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'message': event['message']
        }))

