from rest_framework import serializers
from .models import Payment, PaymentAnalytics
from users.models import CustomUser
from contracts.models import Contract
from projects.models import Project

class UserShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email', 'user_type', 'first_name', 'last_name']

class PaymentSerializer(serializers.ModelSerializer):
    payer = UserShortSerializer(read_only=True)
    recipient = UserShortSerializer(read_only=True)
    project_title = serializers.CharField(source='project.title', read_only=True)
    contract_id = serializers.IntegerField(source='contract.id', read_only=True)
    
    class Meta:
        model = Payment
        fields = [
            'id', 'contract', 'project', 'payer', 'recipient', 'amount', 
            'description', 'payment_type', 'status', 'transaction_id',
            'stripe_payment_intent_id', 'platform_fee', 'net_amount',
            'created_at', 'updated_at', 'processed_at', 'due_date',
            'notes', 'is_milestone', 'milestone_number', 
            'project_title', 'contract_id'
        ]
        read_only_fields = [
            'id', 'payer', 'recipient', 'transaction_id', 'stripe_payment_intent_id',
            'created_at', 'updated_at', 'processed_at', 'net_amount'
        ]

class CreatePaymentSerializer(serializers.ModelSerializer):
    """Serializer for creating new payments"""
    contract_id = serializers.IntegerField(write_only=True)
    recipient_id = serializers.IntegerField(write_only=True, required=False)
    
    class Meta:
        model = Payment
        fields = [
            'contract_id', 'recipient_id', 'amount', 'description', 
            'payment_type', 'due_date', 'notes', 'is_milestone', 'milestone_number'
        ]
    
    def validate_contract_id(self, value):
        try:
            contract = Contract.objects.get(id=value)
            # Ensure user has access to this contract
            user = self.context['request'].user
            if user != contract.client and user != contract.freelancer and not user.is_superuser:
                raise serializers.ValidationError("You don't have access to this contract")
            return value
        except Contract.DoesNotExist:
            raise serializers.ValidationError("Contract not found")
    
    def create(self, validated_data):
        contract_id = validated_data.pop('contract_id')
        recipient_id = validated_data.pop('recipient_id', None)
        
        contract = Contract.objects.get(id=contract_id)
        payer = self.context['request'].user
        
        # Determine recipient
        if recipient_id:
            try:
                recipient = CustomUser.objects.get(id=recipient_id)
            except CustomUser.DoesNotExist:
                raise serializers.ValidationError("Recipient not found")
        else:
            # Default recipient logic
            if payer == contract.client:
                recipient = contract.freelancer
            else:
                recipient = contract.client
        
        # Create payment
        payment = Payment.objects.create(
            contract=contract,
            project=contract.project_proposal.project,
            payer=payer,
            recipient=recipient,
            **validated_data
        )
        
        return payment

class PaymentAnalyticsSerializer(serializers.ModelSerializer):
    user = UserShortSerializer(read_only=True)
    
    class Meta:
        model = PaymentAnalytics
        fields = [
            'user', 'total_earned', 'total_spent', 'total_pending_payments',
            'current_month_earned', 'current_month_spent', 'completed_projects_count',
            'pending_projects_count', 'available_projects_count', 'last_updated'
        ]

class PaymentSummarySerializer(serializers.Serializer):
    """Serializer for payment summary data"""
    total_payments = serializers.IntegerField()
    total_amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    pending_payments = serializers.IntegerField()
    pending_amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    completed_payments = serializers.IntegerField()
    completed_amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    this_month_amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    this_week_amount = serializers.DecimalField(max_digits=15, decimal_places=2)

class DashboardAnalyticsSerializer(serializers.Serializer):
    """Complete dashboard analytics"""
    user_type = serializers.CharField()
    
    # Financial metrics
    total_earned = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_spent = serializers.DecimalField(max_digits=15, decimal_places=2)
    pending_payments = serializers.DecimalField(max_digits=15, decimal_places=2)
    current_month_earned = serializers.DecimalField(max_digits=15, decimal_places=2)
    current_month_spent = serializers.DecimalField(max_digits=15, decimal_places=2)
    
    # Project metrics
    completed_projects = serializers.IntegerField()
    pending_projects = serializers.IntegerField()
    available_projects = serializers.IntegerField()
    
    # Recent payments
    recent_payments = PaymentSerializer(many=True)
    
    # Payment breakdown by type
    payment_breakdown = serializers.DictField()
    
    # Monthly trends (last 6 months)
    monthly_trends = serializers.ListField()