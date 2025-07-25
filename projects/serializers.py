from rest_framework import serializers
from .models import Project, Category, ProjectProposal, ProjectAttachment, SavedProject
from users.models import CustomUser

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'description']

class UserShortSerializer(serializers.ModelSerializer):
    username = serializers.CharField(read_only=True, allow_null=True)
    email = serializers.EmailField(read_only=True, allow_null=True)
    first_name = serializers.CharField(read_only=True, allow_null=True)
    last_name = serializers.CharField(read_only=True, allow_null=True)
    
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email', 'user_type', 'first_name', 'last_name']

class ProjectAttachmentSerializer(serializers.ModelSerializer):
    uploaded_by = UserShortSerializer(read_only=True)
    
    class Meta:
        model = ProjectAttachment
        fields = ['id', 'file', 'filename', 'uploaded_by', 'uploaded_at']

class ProjectProposalSerializer(serializers.ModelSerializer):
    freelancer = UserShortSerializer(read_only=True)
    project_title = serializers.CharField(source='project.title', read_only=True)
    project = serializers.SerializerMethodField(read_only=True)
    estimated_timeline = serializers.CharField(source='proposed_timeline', read_only=True)
    
    class Meta:
        model = ProjectProposal
        fields = ['id', 'project', 'project_title', 'freelancer', 'cover_letter', 'proposed_budget', 
                 'proposed_timeline', 'estimated_timeline', 'status', 'created_at', 'updated_at']
        read_only_fields = ['project', 'freelancer', 'status', 'created_at', 'updated_at']
    
    def get_project(self, obj):
        """Return basic project information"""
        return {
            'id': obj.project.id,
            'title': obj.project.title,
            'status': obj.project.status,
            'budget': str(obj.project.budget),
        }

class ProjectSerializer(serializers.ModelSerializer):
    client = UserShortSerializer(read_only=True, allow_null=True)
    selected_freelancer = UserShortSerializer(read_only=True, allow_null=True)
    category = CategorySerializer(read_only=True, allow_null=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), source='category', write_only=True, required=False, allow_null=True
    )
    project_attachments = ProjectAttachmentSerializer(many=True, read_only=True)
    proposals_count = serializers.SerializerMethodField()
    is_saved = serializers.SerializerMethodField()
    
    class Meta:
        model = Project
        fields = '__all__'
        read_only_fields = ['client', 'created_at', 'updated_at', 'selected_freelancer', 'completed_at']
    
    def get_proposals_count(self, obj):
        return obj.proposals.count()
    
    def get_is_saved(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return SavedProject.objects.filter(user=request.user, project=obj).exists()
        return False

class SavedProjectSerializer(serializers.ModelSerializer):
    project = ProjectSerializer(read_only=True)
    
    class Meta:
        model = SavedProject
        fields = ['id', 'project', 'saved_at']
