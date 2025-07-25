from rest_framework import serializers
from .models import Dispute

class DisputeSerializer(serializers.ModelSerializer):
    created_by = serializers.StringRelatedField(read_only=True)
    resolved_by = serializers.StringRelatedField(read_only=True)
    created_by_name = serializers.SerializerMethodField()
    resolved_by_name = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    project_title = serializers.SerializerMethodField()
    contract_details = serializers.SerializerMethodField()

    class Meta:
        model = Dispute
        fields = [
            'id', 'title', 'description', 'type', 'type_display', 
            'priority', 'priority_display', 'status', 'status_display',
            'project', 'project_title', 'contract', 'contract_details',
            'created_by', 'created_by_name', 'resolved_by', 'resolved_by_name',
            'resolution', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_by', 'resolved_by', 'created_at', 'updated_at']

    def get_created_by_name(self, obj):
        if obj.created_by:
            return f"{obj.created_by.first_name} {obj.created_by.last_name}".strip() or obj.created_by.username
        return None
    
    def get_resolved_by_name(self, obj):
        if obj.resolved_by:
            return f"{obj.resolved_by.first_name} {obj.resolved_by.last_name}".strip() or obj.resolved_by.username
        return None
    
    def get_project_title(self, obj):
        if obj.project:
            return obj.project.title
        return None
    
    def get_contract_details(self, obj):
        if obj.contract:
            return {
                'id': obj.contract.id,
                'status': obj.contract.status,
                'total_payment': str(obj.contract.total_payment),
                'project_title': obj.contract.project_proposal.project.title
            }
        return None

    def create(self, validated_data):
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['created_by'] = request.user
        return super().create(validated_data)

class CreateDisputeSerializer(serializers.ModelSerializer):
    """Simplified serializer for creating disputes - matches frontend interface"""
    project_id = serializers.IntegerField(required=False, allow_null=True)
    contract_id = serializers.IntegerField(required=False, allow_null=True)
    
    class Meta:
        model = Dispute
        fields = ['title', 'description', 'type', 'priority', 'project_id', 'contract_id']
        
    def validate(self, data):
        """Ensure at least one of project_id or contract_id is provided"""
        project_id = data.get('project_id')
        contract_id = data.get('contract_id')
        
        if not project_id and not contract_id:
            raise serializers.ValidationError(
                "Either project_id or contract_id must be provided"
            )
        
        return data
        
    def create(self, validated_data):
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['created_by'] = request.user
            
        # Handle project_id and contract_id
        project_id = validated_data.pop('project_id', None)
        contract_id = validated_data.pop('contract_id', None)
        
        if project_id:
            from projects.models import Project
            try:
                project = Project.objects.get(id=project_id)
                validated_data['project'] = project
            except Project.DoesNotExist:
                raise serializers.ValidationError(f"Project with id {project_id} not found")
        
        if contract_id:
            from contracts.models import Contract
            try:
                contract = Contract.objects.get(id=contract_id)
                validated_data['contract'] = contract
                # If contract is provided but no project, use contract's project
                if not project_id:
                    validated_data['project'] = contract.project_proposal.project
            except Contract.DoesNotExist:
                raise serializers.ValidationError(f"Contract with id {contract_id} not found")
        
        return super().create(validated_data)

