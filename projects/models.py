from django.db import models
from users.models import CustomUser

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

class Project(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    budget = models.DecimalField(max_digits=10, decimal_places=2)
    deadline = models.DateTimeField()
    client = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='projects')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=20, default='open')
    category = models.ForeignKey(Category, null=True, blank=True, on_delete=models.SET_NULL, related_name='projects')
    tags = models.JSONField(default=list, blank=True)
    attachments = models.FileField(upload_to='project_attachments/', null=True, blank=True)
    location = models.CharField(max_length=255, blank=True)
    skills_required = models.JSONField(default=list, blank=True)
    is_public = models.BooleanField(default=True)
    selected_freelancer = models.ForeignKey(CustomUser, null=True, blank=True, related_name='awarded_projects', on_delete=models.SET_NULL)
    completed_at = models.DateTimeField(null=True, blank=True)
    is_featured = models.BooleanField(default=False)
