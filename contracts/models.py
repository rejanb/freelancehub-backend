from django.db import models
from proposals.models import Proposal

class Contract(models.Model):
    proposal = models.OneToOneField(Proposal, on_delete=models.CASCADE, related_name='contract')
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ('active', 'Active'),
            ('completed', 'Completed'),
            ('cancelled', 'Cancelled'),
        ],
        default='active'
    )
    total_payment = models.DecimalField(max_digits=10, decimal_places=2)
    deliverables = models.TextField(blank=True)
    milestones = models.TextField(blank=True)

    def __str__(self):
        return f"Contract for {self.proposal}"