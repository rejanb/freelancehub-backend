from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from users.models import CustomUser
from projects.models import Project
from contracts.models import Contract

# Create your models here.

class Dispute(models.Model):
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('under_review', 'Under Review'),
        ('resolved', 'Resolved'),
        ('rejected', 'Rejected'),
    ]
    
    TYPE_CHOICES = [
        ('payment', 'Payment Issue'),
        ('quality', 'Quality Issue'),
        ('deadline', 'Deadline Issue'),
        ('scope', 'Scope Issue'),
        ('other', 'Other'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    title = models.CharField(max_length=255)
    description = models.TextField()
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='other')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    
    # Direct foreign keys for easier filtering
    project = models.ForeignKey(Project, null=True, blank=True, on_delete=models.CASCADE, related_name='disputes')
    contract = models.ForeignKey(Contract, null=True, blank=True, on_delete=models.CASCADE, related_name='disputes')
    
    created_by = models.ForeignKey(CustomUser, related_name='disputes_created', on_delete=models.CASCADE)
    resolved_by = models.ForeignKey(CustomUser, related_name='disputes_resolved', null=True, blank=True, on_delete=models.SET_NULL)
    resolution = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._original_status = self.status

    def save(self, *args, **kwargs):
        # Store original status for change detection
        if self.pk:
            try:
                original = Dispute.objects.get(pk=self.pk)
                self._original_status = original.status
            except Dispute.DoesNotExist:
                self._original_status = None
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Dispute ({self.status}): {self.title}"
    
    class Meta:
        ordering = ['-created_at']
