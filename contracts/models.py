

from django.db import models
from users.models import CustomUser
from jobs.models import Job

class Proposal(models.Model):
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='contract_job_proposals')
    freelancer = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='contract_user_proposals')
    cover_letter = models.TextField()
    bid_amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    is_accepted = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.freelancer} - {self.job.title}"

class Contract(models.Model):
    proposal = models.OneToOneField(Proposal, on_delete=models.CASCADE, related_name='contract')
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=[
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ], default='active')
    total_payment = models.DecimalField(max_digits=10, decimal_places=2)
    deliverables = models.TextField(blank=True)
    milestones = models.TextField(blank=True)

    def __str__(self):
        return f"Contract for {self.proposal}"