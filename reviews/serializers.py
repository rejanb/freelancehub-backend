from rest_framework import serializers
from .models import Review
from users.models import CustomUser
from django.contrib.contenttypes.models import ContentType

class ReviewSerializer(serializers.ModelSerializer):
    reviewer = serializers.StringRelatedField(read_only=True)
    reviewee = serializers.StringRelatedField()
    content_type = serializers.SlugRelatedField(
        queryset=ContentType.objects.all(),
        slug_field='model'
    )

    class Meta:
        model = Review
        fields = ['id', 'rating', 'comment', 'reviewer', 'reviewee', 'content_type', 'object_id', 'created_at']
        read_only_fields = ['id', 'reviewer', 'created_at']

    def create(self, validated_data):
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['reviewer'] = request.user
        return super().create(validated_data)

