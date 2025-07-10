from django.db import models
from django.conf import settings
from jobs.models import Job
from contracts.models import Contract

class Chat(models.Model):
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_messages'
    )
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='received_messages'
    )
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    job = models.ForeignKey(Job, on_delete=models.CASCADE, null=True, blank=True, related_name='messages')
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE, null=True, blank=True, related_name='messages')

    def __str__(self):
        return f"From {self.sender} to {self.recipient}: {self.content[:30]}"