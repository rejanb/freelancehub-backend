from django.contrib import admin
from .models import Project, Category, ProjectProposal, ProjectAttachment, SavedProject

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']
    search_fields = ['name']

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ['title', 'client', 'category', 'status', 'budget', 'deadline', 'created_at']
    list_filter = ['status', 'category', 'is_public', 'is_featured', 'created_at']
    search_fields = ['title', 'description', 'client__username']
    readonly_fields = ['created_at', 'updated_at', 'completed_at']

@admin.register(ProjectProposal)
class ProjectProposalAdmin(admin.ModelAdmin):
    list_display = ['project', 'freelancer', 'status', 'proposed_budget', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['project__title', 'freelancer__username']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(ProjectAttachment)
class ProjectAttachmentAdmin(admin.ModelAdmin):
    list_display = ['project', 'filename', 'uploaded_by', 'uploaded_at']
    list_filter = ['uploaded_at']
    search_fields = ['project__title', 'filename', 'uploaded_by__username']
    readonly_fields = ['uploaded_at']

@admin.register(SavedProject)
class SavedProjectAdmin(admin.ModelAdmin):
    list_display = ['user', 'project', 'saved_at']
    list_filter = ['saved_at']
    search_fields = ['user__username', 'project__title']
    readonly_fields = ['saved_at']
