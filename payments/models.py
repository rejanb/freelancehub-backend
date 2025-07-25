from django.db import models
from django.conf import settings
from contracts.models import Contract
from projects.models import Project
from django.utils import timezone
from datetime import datetime, timedelta

class Payment(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
        ('cancelled', 'Cancelled')
    ]
    
    PAYMENT_TYPE_CHOICES = [
        ('project_payment', 'Project Payment'),
        ('milestone_payment', 'Milestone Payment'),
        ('bonus_payment', 'Bonus Payment'),
        ('refund', 'Refund'),
        ('penalty', 'Penalty'),
        ('platform_fee', 'Platform Fee')
    ]
    
    # Core payment fields
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE, related_name='payments')
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='payments', null=True, blank=True)
    payer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='payments_made')
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='payments_received')
    
    # Payment details
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField()
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPE_CHOICES, default='project_payment')
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    
    # Transaction details
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    stripe_payment_intent_id = models.CharField(max_length=100, blank=True, null=True)
    platform_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    net_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    due_date = models.DateTimeField(null=True, blank=True)
    
    # Additional metadata
    notes = models.TextField(blank=True)
    is_milestone = models.BooleanField(default=False)
    milestone_number = models.IntegerField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['payer', '-created_at']),
            models.Index(fields=['recipient', '-created_at']),
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['payment_type', '-created_at']),
        ]
    
    def __str__(self):
        return f"Payment {self.id}: ${self.amount} from {self.payer.username} to {self.recipient.username}"
    
    def save(self, *args, **kwargs):
        # Calculate net amount (amount minus platform fee)
        if self.net_amount is None:
            self.net_amount = self.amount - self.platform_fee
        
        # Set processed_at when status changes to completed
        if self.status == 'completed' and not self.processed_at:
            self.processed_at = timezone.now()
            
        # Set project from contract if not set
        if not self.project and self.contract:
            self.project = self.contract.project_proposal.project
            
        super().save(*args, **kwargs)


class PaymentAnalytics(models.Model):
    """Store aggregated payment analytics for performance"""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='payment_analytics')
    
    # Lifetime totals
    total_earned = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_spent = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_pending_payments = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Monthly totals
    current_month_earned = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    current_month_spent = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Project counts
    completed_projects_count = models.IntegerField(default=0)
    pending_projects_count = models.IntegerField(default=0)
    available_projects_count = models.IntegerField(default=0)  # For freelancers - projects they can bid on
    
    # Last updated
    last_updated = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Analytics for {self.user.username}"
    
    @classmethod
    def update_analytics(cls, user):
        """Update analytics for a specific user"""
        analytics, created = cls.objects.get_or_create(user=user)
        
        # Current month date range
        now = timezone.now()
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        if user.user_type == 'freelancer':
            # Freelancer analytics
            completed_payments = Payment.objects.filter(
                recipient=user,
                status='completed'
            )
            
            analytics.total_earned = sum(p.net_amount or 0 for p in completed_payments)
            analytics.current_month_earned = sum(
                p.net_amount or 0 for p in completed_payments.filter(processed_at__gte=start_of_month)
            )
            
            # Project counts for freelancer
            from contracts.models import Contract
            analytics.completed_projects_count = Contract.objects.filter(
                project_proposal__freelancer=user,
                status='completed'
            ).count()
            
            analytics.pending_projects_count = Contract.objects.filter(
                project_proposal__freelancer=user,
                status='active'
            ).count()
            
            # Available projects (projects without accepted proposals that freelancer hasn't bid on)
            from projects.models import Project, ProjectProposal
            freelancer_proposals = ProjectProposal.objects.filter(freelancer=user).values_list('project_id', flat=True)
            analytics.available_projects_count = Project.objects.filter(
                status='open'
            ).exclude(
                id__in=freelancer_proposals
            ).exclude(
                proposals__status='accepted'
            ).count()
            
        elif user.user_type == 'client':
            # Client analytics
            made_payments = Payment.objects.filter(
                payer=user,
                status='completed'
            )
            
            analytics.total_spent = sum(p.amount for p in made_payments)
            analytics.current_month_spent = sum(
                p.amount for p in made_payments.filter(processed_at__gte=start_of_month)
            )
            
            # Pending payments
            analytics.total_pending_payments = sum(
                p.amount for p in Payment.objects.filter(payer=user, status='pending')
            )
            
            # Project counts for client
            from contracts.models import Contract
            analytics.completed_projects_count = Contract.objects.filter(
                project_proposal__project__client=user,
                status='completed'
            ).count()
            
            analytics.pending_projects_count = Contract.objects.filter(
                project_proposal__project__client=user,
                status='active'
            ).count()
            
            # Available projects for client = their open projects
            analytics.available_projects_count = Project.objects.filter(
                client=user,
                status='open'
            ).count()
        
        analytics.save()
        return analytics