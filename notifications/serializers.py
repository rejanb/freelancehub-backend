from rest_framework import serializers
from .models import Notification
from django.contrib.contenttypes.models import ContentType

class NotificationSerializer(serializers.ModelSerializer):
    content_type = serializers.SlugRelatedField(
        queryset=ContentType.objects.all(),
        slug_field='model',
        required=False,
        allow_null=True
    )
    class Meta:
        model = Notification
        fields = ['id', 'user', 'message', 'notification_type', 'is_read', 'content_type', 'object_id', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']

