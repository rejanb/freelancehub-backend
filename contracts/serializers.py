from rest_framework import serializers
from .models import Contract, ContractDocument
from users.models import CustomUser

class UserShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email', 'user_type', 'first_name', 'last_name']

class ContractDocumentSerializer(serializers.ModelSerializer):
    uploaded_by = UserShortSerializer(read_only=True)
    
    class Meta:
        model = ContractDocument
        fields = ['id', 'file', 'filename', 'uploaded_by', 'uploaded_at', 'document_type']

from rest_framework import serializers
from .models import Contract, ContractDocument
from users.models import CustomUser
from projects.models import Project, ProjectProposal
from django.utils import timezone

class UserShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email', 'user_type', 'first_name', 'last_name']

class ContractDocumentSerializer(serializers.ModelSerializer):
    uploaded_by = UserShortSerializer(read_only=True)
    file_url = serializers.SerializerMethodField()
    file_size = serializers.SerializerMethodField()
    
    class Meta:
        model = ContractDocument
        fields = ['id', 'file', 'file_url', 'filename', 'uploaded_by', 'uploaded_at', 'document_type', 'file_size']
    
    def get_file_url(self, obj):
        if obj.file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.file.url)
            return obj.file.url
        return None
    
    def get_file_size(self, obj):
        if obj.file:
            return obj.file.size
        return None

class ContractSerializer(serializers.ModelSerializer):
    client = UserShortSerializer(read_only=True)
    freelancer = UserShortSerializer(read_only=True)
    project_title = serializers.CharField(source='project_proposal.project.title', read_only=True)
    project_id = serializers.CharField(source='project_proposal.project.id', read_only=True)
    project_description = serializers.CharField(source='project_proposal.project.description', read_only=True)
    project_category = serializers.CharField(source='project_proposal.project.category', read_only=True)
    documents = ContractDocumentSerializer(many=True, read_only=True)
    
    # Calculated fields
    days_remaining = serializers.SerializerMethodField()
    progress_percentage = serializers.SerializerMethodField()
    is_overdue = serializers.SerializerMethodField()
    can_be_completed = serializers.SerializerMethodField()
    
    class Meta:
        model = Contract
        fields = [
            'id', 'project_proposal', 'project_id', 'project_title', 'project_description', 'project_category',
            'client', 'freelancer', 'start_date', 'end_date', 'status', 
            'total_payment', 'deliverables', 'milestones', 'created_at', 
            'updated_at', 'signed_by_client', 'signed_by_freelancer', 
            'cancellation_reason', 'documents', 'days_remaining', 'progress_percentage',
            'is_overdue', 'can_be_completed'
        ]
    
    def get_days_remaining(self, obj):
        if obj.end_date and obj.status == 'active':
            remaining = (obj.end_date - timezone.now().date()).days
            return max(0, remaining)
        return None
    
    def get_progress_percentage(self, obj):
        if obj.start_date and obj.end_date:
            total_days = (obj.end_date - obj.start_date).days
            if total_days > 0:
                elapsed_days = (timezone.now().date() - obj.start_date).days
                return min(100, max(0, (elapsed_days / total_days) * 100))
        return 0
    
    def get_is_overdue(self, obj):
        if obj.end_date and obj.status == 'active':
            return timezone.now().date() > obj.end_date
        return False
    
    def get_can_be_completed(self, obj):
        # Contract can be completed if it's active and both parties have signed
        return (obj.status == 'active' and 
                obj.signed_by_client and 
                obj.signed_by_freelancer)

class ContractDetailSerializer(ContractSerializer):
    """Extended serializer with more details for individual contract view"""
    project = serializers.SerializerMethodField()
    payment_info = serializers.SerializerMethodField()
    timeline_info = serializers.SerializerMethodField()
    
    class Meta(ContractSerializer.Meta):
        fields = ContractSerializer.Meta.fields + ['project', 'payment_info', 'timeline_info']
    
    def get_project(self, obj):
        project = obj.project_proposal.project
        return {
            'id': project.id,
            'title': project.title,
            'description': project.description,
            'category': project.category,
            'budget': project.budget,
            'status': project.status,
            'created_at': project.created_at,
            'tags': project.tags,
        }
    
    def get_payment_info(self, obj):
        # Get payment information related to this contract
        payments = obj.payments.all()
        total_paid = sum(p.amount for p in payments.filter(status='completed'))
        pending_payments = sum(p.amount for p in payments.filter(status='pending'))
        
        return {
            'total_amount': obj.total_payment,
            'total_paid': total_paid,
            'pending_amount': pending_payments,
            'remaining_amount': obj.total_payment - total_paid,
            'payment_count': payments.count(),
        }
    
    def get_timeline_info(self, obj):
        return {
            'start_date': obj.start_date,
            'end_date': obj.end_date,
            'created_at': obj.created_at,
            'days_elapsed': (timezone.now().date() - obj.start_date).days if obj.start_date else 0,
            'total_duration': (obj.end_date - obj.start_date).days if obj.start_date and obj.end_date else 0,
        }

class CreateContractSerializer(serializers.ModelSerializer):
    """Serializer for creating contracts"""
    proposal_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = Contract
        fields = [
            'proposal_id', 'start_date', 'end_date', 'total_payment', 
            'deliverables', 'milestones'
        ]
    
    def validate_proposal_id(self, value):
        try:
            proposal = ProjectProposal.objects.get(id=value)
            # Verify proposal is accepted
            if proposal.status != 'accepted':
                raise serializers.ValidationError("Only accepted proposals can be converted to contracts")
            
            # Check if contract already exists
            if hasattr(proposal, 'contract'):
                raise serializers.ValidationError("Contract already exists for this proposal")
            
            return value
        except ProjectProposal.DoesNotExist:
            raise serializers.ValidationError("Proposal not found")
    
    def validate(self, data):
        # Validate date range
        if data.get('end_date') and data.get('start_date'):
            if data['end_date'] <= data['start_date']:
                raise serializers.ValidationError("End date must be after start date")
        
        return data
    
    def create(self, validated_data):
        proposal_id = validated_data.pop('proposal_id')
        proposal = ProjectProposal.objects.get(id=proposal_id)
        
        contract = Contract.objects.create(
            project_proposal=proposal,
            **validated_data
        )
        
        return contract

class ContractSummarySerializer(serializers.Serializer):
    """Serializer for contract summary statistics"""
    total_contracts = serializers.IntegerField()
    active_contracts = serializers.IntegerField()
    completed_contracts = serializers.IntegerField()
    cancelled_contracts = serializers.IntegerField()
    total_value = serializers.DecimalField(max_digits=15, decimal_places=2)
    active_value = serializers.DecimalField(max_digits=15, decimal_places=2)
    completed_value = serializers.DecimalField(max_digits=15, decimal_places=2)
    average_contract_value = serializers.DecimalField(max_digits=15, decimal_places=2)
    contracts_this_month = serializers.IntegerField()
    overdue_contracts = serializers.IntegerField()