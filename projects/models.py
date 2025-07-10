from django.db import models
from users.models import CustomUser

class Project(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    budget = models.DecimalField(max_digits=10, decimal_places=2)
    deadline = models.DateTimeField()
    client = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='projects')
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, default='open')
