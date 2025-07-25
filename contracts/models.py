from django.db import models
from users.models import CustomUser
from projects.models import ProjectProposal

def contract_file_upload_path(instance, filename):
    """Generate upload path for contract files"""
    return f'contracts/{instance.contract.id}/{filename}'

class Contract(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('terminated', 'Terminated'),
    ]
    
    # Link to project proposal (not the old job proposal)
    project_proposal = models.OneToOneField(
        ProjectProposal, 
        on_delete=models.CASCADE, 
        related_name='contract'
    )
    
    # Contract details
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    total_payment = models.DecimalField(max_digits=10, decimal_places=2)
    deliverables = models.TextField(blank=True)
    milestones = models.TextField(blank=True)
    
    # Signing information
    signed_by_client = models.BooleanField(default=False)
    signed_by_freelancer = models.BooleanField(default=False)
    client_signed_at = models.DateTimeField(null=True, blank=True)
    freelancer_signed_at = models.DateTimeField(null=True, blank=True)
    
    # Termination information
    termination_reason = models.TextField(blank=True)
    terminated_by = models.ForeignKey(
        CustomUser, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='terminated_contracts'
    )
    terminated_at = models.DateTimeField(null=True, blank=True)
    
    # Legacy field (keeping for compatibility)
    cancellation_reason = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Contract for {self.project_proposal.project.title}"
    
    @property
    def client(self):
        return self.project_proposal.project.client
    
    @property
    def freelancer(self):
        return self.project_proposal.freelancer
    
    @property
    def project(self):
        return self.project_proposal.project
    
    @property
    def is_fully_signed(self):
        return self.signed_by_client and self.signed_by_freelancer

class ContractDocument(models.Model):
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE, related_name='documents')
    file = models.FileField(upload_to=contract_file_upload_path)
    filename = models.CharField(max_length=255)
    uploaded_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    document_type = models.CharField(
        max_length=50,
        choices=[
            ('contract', 'Contract Document'),
            ('amendment', 'Amendment'),
            ('deliverable', 'Deliverable'),
            ('other', 'Other'),
        ],
        default='contract'
    )
    
    def __str__(self):
        return f"{self.contract} - {self.filename}"