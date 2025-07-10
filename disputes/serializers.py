from rest_framework import serializers
from .models import Dispute
from django.contrib.contenttypes.models import ContentType

class DisputeSerializer(serializers.ModelSerializer):
    content_type = serializers.SlugRelatedField(
        queryset=ContentType.objects.all(),
        slug_field='model'
    )
    created_by = serializers.StringRelatedField(read_only=True)
    resolved_by = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Dispute
        fields = [
            'id', 'reason', 'description', 'status', 'created_by', 'resolved_by',
            'resolution', 'content_type', 'object_id', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_by', 'resolved_by', 'created_at', 'updated_at']

    def create(self, validated_data):
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['created_by'] = request.user
        return super().create(validated_data)

