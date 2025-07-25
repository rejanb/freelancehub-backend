from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import ChatRoom, Message, Chat

User = get_user_model()


class UserBasicSerializer(serializers.ModelSerializer):
    """Basic user serializer for chat contexts"""
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'profile_picture']
        read_only_fields = ['id']


class MessageSerializer(serializers.ModelSerializer):
    """Message serializer with file support"""
    sender = UserBasicSerializer(read_only=True)
    read_by_users = UserBasicSerializer(source='read_by', many=True, read_only=True)
    is_read_by_current_user = serializers.SerializerMethodField()
    attachment_url = serializers.SerializerMethodField()
    file_size_formatted = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = [
            'id', 'chat_room', 'sender', 'content', 'message_type',
            'attachment', 'attachment_name', 'attachment_size', 'attachment_type',
            'attachment_url', 'file_size_formatted', 'is_edited', 'edited_at',
            'read_by_users', 'is_read_by_current_user', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'sender', 'is_edited', 'edited_at', 'created_at', 'updated_at'
        ]

    def get_is_read_by_current_user(self, obj):
        request = self.context.get('request')
        if request and hasattr(request, 'user') and request.user.is_authenticated:
            return obj.is_read_by(request.user)
        return False

    def get_attachment_url(self, obj):
        if obj.attachment:
            try:
                request = self.context.get('request')
                if request:
                    return request.build_absolute_uri(obj.attachment.url)
                else:
                    # Fallback to relative URL if no request context
                    return obj.attachment.url
            except Exception:
                # Fallback to relative URL if build_absolute_uri fails
                return obj.attachment.url
        return None

    def get_file_size_formatted(self, obj):
        if obj.attachment_size:
            # Convert bytes to human readable format
            for unit in ['B', 'KB', 'MB', 'GB']:
                if obj.attachment_size < 1024.0:
                    return f"{obj.attachment_size:.1f} {unit}"
                obj.attachment_size /= 1024.0
            return f"{obj.attachment_size:.1f} TB"
        return None

    def create(self, validated_data):
        # Set sender from request user
        validated_data['sender'] = self.context['request'].user
        
        # Handle file attachment
        attachment = validated_data.get('attachment')
        if attachment:
            validated_data['attachment_name'] = attachment.name
            validated_data['attachment_size'] = attachment.size
            validated_data['attachment_type'] = attachment.content_type
            validated_data['message_type'] = 'image' if attachment.content_type.startswith('image/') else 'file'
        
        return super().create(validated_data)


class ChatRoomSerializer(serializers.ModelSerializer):
    """Chat room serializer with participants and last message"""
    participants = UserBasicSerializer(many=True, read_only=True)
    participant_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    display_name = serializers.SerializerMethodField()

    class Meta:
        model = ChatRoom
        fields = [
            'id', 'name', 'is_group', 'participants', 'participant_ids',
            'last_message',
            'unread_count', 'display_name', 'job', 'contract',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_last_message(self, obj):
        """Get the last message in this chat room"""
        last_message = obj.messages.order_by('-created_at').first()
        if last_message:
            return {
                'id': last_message.id,
                'content': last_message.content,
                'sender': {
                    'id': last_message.sender.id,
                    'username': last_message.sender.username,
                    'first_name': last_message.sender.first_name,
                    'last_name': last_message.sender.last_name,
                },
                'created_at': last_message.created_at,
                'message_type': last_message.message_type
            }
        return None

    def get_unread_count(self, obj):
        request = self.context.get('request')
        if request and hasattr(request, 'user') and request.user.is_authenticated:
            return obj.get_unread_count(request.user)
        return 0

    def get_display_name(self, obj):
        request = self.context.get('request')
        if obj.name:
            return obj.name
        
        if request and hasattr(request, 'user') and request.user.is_authenticated:
            other_participants = obj.participants.exclude(id=request.user.id)
            if other_participants.exists():
                if len(other_participants) == 1:
                    user = other_participants.first()
                    return f"{user.first_name} {user.last_name}" if user.first_name else user.username
                else:
                    return f"Group chat ({other_participants.count()} members)"
        
        return "Unknown Chat"

    def create(self, validated_data):
        participant_ids = validated_data.pop('participant_ids', [])
        chat_room = super().create(validated_data)
        
        # Add current user as participant
        chat_room.participants.add(self.context['request'].user)
        
        # Add other participants
        if participant_ids:
            chat_room.participants.add(*participant_ids)
        
        return chat_room


class MessageCreateSerializer(serializers.Serializer):
    """Serializer for creating messages via API"""
    chat_room_id = serializers.IntegerField()
    content = serializers.CharField(required=False, allow_blank=True)
    attachment = serializers.FileField(required=False)

    def validate_chat_room_id(self, value):
        try:
            chat_room = ChatRoom.objects.get(id=value)
            # Check if user is participant
            if not chat_room.participants.filter(id=self.context['request'].user.id).exists():
                raise serializers.ValidationError("You are not a participant in this chat room.")
            return value
        except ChatRoom.DoesNotExist:
            raise serializers.ValidationError("Chat room does not exist.")

    def validate(self, data):
        if not data.get('content') and not data.get('attachment'):
            raise serializers.ValidationError("Either content or attachment is required.")
        return data


# Legacy Chat serializer for backward compatibility
class LegacyChatSerializer(serializers.ModelSerializer):
    """Legacy chat serializer - deprecated"""
    sender = UserBasicSerializer(read_only=True)
    recipient = UserBasicSerializer(read_only=True)

    class Meta:
        model = Chat
        fields = ['id', 'sender', 'recipient', 'content', 'job', 'contract', 'created_at']
        read_only_fields = ['id', 'sender', 'created_at']
