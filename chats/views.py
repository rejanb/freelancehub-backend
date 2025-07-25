from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q, Prefetch
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import json

from .models import ChatRoom, Message, Chat
from .serializers import (
    ChatRoomSerializer, MessageSerializer, MessageCreateSerializer, 
    LegacyChatSerializer, UserBasicSerializer
)

User = get_user_model()

class MessagePagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 100

class ChatRoomViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing chat rooms
    """
    serializer_class = ChatRoomSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Return chat rooms where the user is a participant"""
        return ChatRoom.objects.filter(
            participants=self.request.user
        ).prefetch_related('participants').distinct()

    def perform_create(self, serializer):
        """Create a new chat room"""
        chat_room = serializer.save()
        # Add the current user as a participant
        chat_room.participants.add(self.request.user)

    @action(detail=True, methods=['post'])
    def add_participant(self, request, pk=None):
        """Add a participant to the chat room"""
        chat_room = self.get_object()
        user_id = request.data.get('user_id')
        
        if not user_id:
            return Response({'error': 'user_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.get(id=user_id)
            chat_room.participants.add(user)
            
            # Notify WebSocket
            self._notify_websocket(chat_room.id, {
                'type': 'user_joined',
                'user_id': user.id,
                'username': user.username
            })
            
            return Response({'message': 'User added successfully'})
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['post'])
    def remove_participant(self, request, pk=None):
        """Remove a participant from the chat room"""
        chat_room = self.get_object()
        user_id = request.data.get('user_id')
        
        if not user_id:
            return Response({'error': 'user_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.get(id=user_id)
            chat_room.participants.remove(user)
            
            # Notify WebSocket
            self._notify_websocket(chat_room.id, {
                'type': 'user_left',
                'user_id': user.id,
                'username': user.username
            })
            
            return Response({'message': 'User removed successfully'})
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['post'])
    def mark_all_read(self, request, pk=None):
        """Mark all messages in the chat room as read"""
        chat_room = self.get_object()
        chat_room.mark_all_read(request.user)
        return Response({'message': 'All messages marked as read'})

    @action(detail=False, methods=['post'])
    def create_private_chat(self, request):
        """Create or get existing private chat between two users"""
        other_user_id = request.data.get('other_user_id')
        
        if not other_user_id:
            return Response({'error': 'other_user_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            other_user = User.objects.get(id=other_user_id)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Check if private chat already exists
        existing_chat = ChatRoom.objects.filter(
            participants=request.user,
            is_group=False
        ).filter(
            participants=other_user
        ).first()
        
        if existing_chat:
            serializer = self.get_serializer(existing_chat)
            return Response(serializer.data)
        
        # Create new private chat
        chat_room = ChatRoom.objects.create(is_group=False)
        chat_room.participants.add(request.user, other_user)
        
        serializer = self.get_serializer(chat_room)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'])
    def can_initiate_chat(self, request):
        """Check if user can initiate chat with another user"""
        target_user_id = request.data.get('target_user_id')
        context_type = request.data.get('context_type')
        context_id = request.data.get('context_id')
        
        if not target_user_id:
            return Response({'error': 'target_user_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            target_user = User.objects.get(id=target_user_id)
        except User.DoesNotExist:
            return Response({'can_chat': False, 'reason': 'User not found'})
        
        # Basic validation - users can always chat with each other
        # You can add more complex business logic here based on context
        return Response({'can_chat': True})

    def _notify_websocket(self, chat_room_id, message):
        """Send message to WebSocket group"""
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'chat_{chat_room_id}',
            message
        )

class MessageViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing messages
    """
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = MessagePagination

    def get_queryset(self):
        """Return messages from chat rooms where the user is a participant"""
        chat_room_id = self.request.query_params.get('chat_room')
        queryset = Message.objects.filter(
            chat_room__participants=self.request.user
        ).select_related('sender', 'chat_room').prefetch_related('read_by')
        
        if chat_room_id:
            queryset = queryset.filter(chat_room_id=chat_room_id)
        
        return queryset.order_by('-created_at')

    def perform_create(self, serializer):
        """Create a new message and notify WebSocket"""
        message = serializer.save(sender=self.request.user)
        
        # Update chat room's updated_at timestamp
        message.chat_room.save(update_fields=['updated_at'])
        
        # Notify WebSocket
        channel_layer = get_channel_layer()
        message_data = MessageSerializer(message, context={'request': self.request}).data
        
        async_to_sync(channel_layer.group_send)(
            f'chat_{message.chat_room.id}',
            {
                'type': 'chat_message',
                'message': message_data
            }
        )

    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """Mark a specific message as read"""
        message = self.get_object()
        message.mark_as_read(request.user)
        return Response({'message': 'Message marked as read'})

    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """Get count of unread messages for the current user"""
        # Count messages in chat rooms where user is participant but hasn't read the message
        unread_count = Message.objects.filter(
            chat_room__participants=request.user
        ).exclude(
            read_by=request.user
        ).count()
        
        return Response({'unread_count': unread_count})

    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        """Mark all messages as read for the current user"""
        chat_room_id = request.data.get('chat_room_id')
        
        if chat_room_id:
            # Mark all messages in specific chat room as read
            messages = Message.objects.filter(
                chat_room_id=chat_room_id,
                chat_room__participants=request.user
            ).exclude(read_by=request.user)
            
            for message in messages:
                message.mark_as_read(request.user)
                
            return Response({
                'message': f'All messages in chat room {chat_room_id} marked as read',
                'count': messages.count()
            })
        else:
            # Mark all messages for user as read
            messages = Message.objects.filter(
                chat_room__participants=request.user
            ).exclude(read_by=request.user)
            
            for message in messages:
                message.mark_as_read(request.user)
                
            return Response({
                'message': 'All messages marked as read',
                'count': messages.count()
            })

    @action(detail=False, methods=['post'])
    def send_message(self, request):
        """Send a message using simplified API"""
        serializer = MessageCreateSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            chat_room_id = serializer.validated_data['chat_room_id']
            content = serializer.validated_data.get('content', '')
            attachment = serializer.validated_data.get('attachment')
            
            # Get chat room
            chat_room = get_object_or_404(ChatRoom, id=chat_room_id)
            
            # Create message
            message_data = {
                'chat_room': chat_room,
                'content': content,
                'sender': request.user
            }
            
            if attachment:
                message_data.update({
                    'attachment': attachment,
                    'attachment_name': attachment.name,
                    'attachment_size': attachment.size,
                    'attachment_type': attachment.content_type,
                    'message_type': 'image' if attachment.content_type.startswith('image/') else 'file'
                })
            
            message = Message.objects.create(**message_data)
            
            # Update chat room timestamp
            chat_room.save(update_fields=['updated_at'])
            
            # Notify WebSocket
            channel_layer = get_channel_layer()
            message_serializer = MessageSerializer(message, context={'request': request})
            
            async_to_sync(channel_layer.group_send)(
                f'chat_{chat_room.id}',
                {
                    'type': 'chat_message',
                    'message': message_serializer.data
                }
            )
            
            return Response(message_serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LegacyChatViewSet(viewsets.ModelViewSet):
    """
    Legacy chat ViewSet for backward compatibility
    """
    serializer_class = LegacyChatSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Return chats where user is sender or recipient"""
        return Chat.objects.filter(
            Q(sender=self.request.user) | Q(recipient=self.request.user)
        ).select_related('sender', 'recipient').order_by('-created_at')

    def perform_create(self, serializer):
        """Create a legacy chat message"""
        serializer.save(sender=self.request.user)
