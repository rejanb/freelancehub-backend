from django.shortcuts import render
from rest_framework import generics, permissions, viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Notification
from .serializers import NotificationSerializer
from .utils import send_notification_to_user
import logging

logger = logging.getLogger(__name__)

class NotificationViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user).order_by('-created_at')

    def perform_create(self, serializer):
        notification = serializer.save(user=self.request.user)
        
        # Send real-time notification via WebSocket
        try:
            send_notification_to_user(
                user_id=self.request.user.id,
                notification_data={
                    'id': notification.id,
                    'title': notification.title,
                    'message': notification.message,
                    'type': notification.notification_type,
                    'is_read': notification.is_read,
                    'created_at': notification.created_at.isoformat(),
                }
            )
            logger.info(f"Real-time notification sent to user {self.request.user.id}")
        except Exception as e:
            logger.error(f"Failed to send real-time notification: {e}")

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def read(self, request, pk=None):
        """Mark a specific notification as read"""
        try:
            notification = self.get_object()
            notification.is_read = True
            notification.save()
            
            # Send real-time update via WebSocket
            try:
                send_notification_to_user(
                    user_id=request.user.id,
                    notification_data={
                        'type': 'notification_read',
                        'notification_id': notification.id,
                        'is_read': True
                    }
                )
            except Exception as e:
                logger.error(f"Failed to send real-time read status: {e}")
            
            serializer = self.get_serializer(notification)
            return Response(serializer.data)
        except Notification.DoesNotExist:
            return Response({'error': 'Notification not found'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def mark_all_read(self, request):
        """Mark all notifications as read for the current user"""
        updated_count = Notification.objects.filter(
            user=request.user, 
            is_read=False
        ).update(is_read=True)
        
        # Send real-time update via WebSocket
        try:
            send_notification_to_user(
                user_id=request.user.id,
                notification_data={
                    'type': 'all_notifications_read',
                    'updated_count': updated_count
                }
            )
        except Exception as e:
            logger.error(f"Failed to send real-time mark all read: {e}")
        
        return Response({
            'status': 'success',
            'message': f'{updated_count} notifications marked as read'
        })

    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def clear_all(self, request):
        """Delete all notifications for the current user"""
        deleted_count, _ = Notification.objects.filter(user=request.user).delete()
        
        # Send real-time update via WebSocket
        try:
            send_notification_to_user(
                user_id=request.user.id,
                notification_data={
                    'type': 'all_notifications_cleared',
                    'deleted_count': deleted_count
                }
            )
        except Exception as e:
            logger.error(f"Failed to send real-time clear all: {e}")
        
        return Response({
            'status': 'success',
            'message': f'{deleted_count} notifications deleted'
        })

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def unread_count(self, request):
        """Get count of unread notifications"""
        count = Notification.objects.filter(user=request.user, is_read=False).count()
        return Response({'unread_count': count})

# Legacy views for backward compatibility
class NotificationListCreateView(generics.ListCreateAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user).order_by('-created_at')

    def perform_create(self, serializer):
        notification = serializer.save(user=self.request.user)
        
        # Send real-time notification via WebSocket
        try:
            send_notification_to_user(
                user_id=self.request.user.id,
                notification_data={
                    'id': notification.id,
                    'title': notification.title,
                    'message': notification.message,
                    'type': notification.notification_type,
                    'is_read': notification.is_read,
                    'created_at': notification.created_at.isoformat(),
                }
            )
        except Exception as e:
            logger.error(f"Failed to send real-time notification: {e}")

class NotificationMarkReadView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            notification = Notification.objects.get(pk=pk, user=request.user)
            notification.is_read = True
            notification.save()
            
            # Send real-time update via WebSocket
            try:
                send_notification_to_user(
                    user_id=request.user.id,
                    notification_data={
                        'type': 'notification_read',
                        'notification_id': notification.id,
                        'is_read': True
                    }
                )
            except Exception as e:
                logger.error(f"Failed to send real-time read status: {e}")
            
            return Response({'status': 'marked as read'})
        except Notification.DoesNotExist:
            return Response({'error': 'Notification not found'}, status=status.HTTP_404_NOT_FOUND)
