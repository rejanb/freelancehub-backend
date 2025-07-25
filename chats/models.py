from django.db import models
from django.conf import settings
from jobs.models import Job
from contracts.models import Contract
import os

def chat_file_upload_path(instance, filename):
    """Generate upload path for chat files"""
    return os.path.join('chat_files', str(instance.chat_room.id), filename)

class ChatRoom(models.Model):
    """Chat room model supporting both private and group chats"""
    name = models.CharField(max_length=255, blank=True, null=True)
    participants = models.ManyToManyField(
        settings.AUTH_USER_MODEL, 
        related_name='chat_rooms'
    )
    is_group = models.BooleanField(default=False)
    job = models.ForeignKey(
        Job, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='chat_rooms'
    )
    contract = models.ForeignKey(
        Contract, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='chat_rooms'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        if self.name:
            return self.name
        participants = list(self.participants.all()[:2])
        if len(participants) >= 2:
            return f"Chat between {participants[0].username} and {participants[1].username}"
        elif len(participants) == 1:
            return f"Chat with {participants[0].username}"
        return f"Chat Room {self.id}"

    def get_unread_count(self, user):
        """Get unread message count for a specific user"""
        return self.messages.exclude(read_by=user).exclude(sender=user).count()

    @property
    def last_message(self):
        """Get the last message in this chat room"""
        return self.messages.order_by('-created_at').first()

    def mark_all_read(self, user):
        """Mark all messages as read for a specific user"""
        unread_messages = self.messages.exclude(read_by=user).exclude(sender=user)
        for message in unread_messages:
            message.read_by.add(user)

class Message(models.Model):
    """Message model with support for text, images, and files"""
    MESSAGE_TYPES = [
        ('text', 'Text'),
        ('image', 'Image'),
        ('file', 'File'),
    ]

    chat_room = models.ForeignKey(
        ChatRoom, 
        on_delete=models.CASCADE, 
        related_name='messages'
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='sent_chat_messages'
    )
    content = models.TextField(blank=True)
    message_type = models.CharField(
        max_length=10, 
        choices=MESSAGE_TYPES, 
        default='text'
    )
    
    # File attachment fields
    attachment = models.FileField(
        upload_to=chat_file_upload_path, 
        null=True, 
        blank=True
    )
    attachment_name = models.CharField(max_length=255, blank=True)
    attachment_size = models.PositiveIntegerField(null=True, blank=True)
    attachment_type = models.CharField(max_length=100, blank=True)
    
    # Message status
    is_edited = models.BooleanField(default=False)
    edited_at = models.DateTimeField(null=True, blank=True)
    read_by = models.ManyToManyField(
        settings.AUTH_USER_MODEL, 
        blank=True, 
        related_name='read_messages'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Message from {self.sender.username} in {self.chat_room}"

    def is_read_by(self, user):
        """Check if message is read by a specific user"""
        return self.read_by.filter(id=user.id).exists()

    def mark_as_read(self, user):
        """Mark message as read by a specific user"""
        if user != self.sender:
            self.read_by.add(user)

# Legacy Chat model for backward compatibility
class Chat(models.Model):
    """Legacy chat model - deprecated, use ChatRoom and Message instead"""
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_legacy_messages'
    )
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='received_legacy_messages'
    )
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    job = models.ForeignKey(Job, on_delete=models.CASCADE, null=True, blank=True, related_name='legacy_messages')
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE, null=True, blank=True, related_name='legacy_messages')

    def __str__(self):
        return f"From {self.sender} to {self.recipient}: {self.content[:30]}"

    class Meta:
        verbose_name = "Legacy Chat"
        verbose_name_plural = "Legacy Chats"