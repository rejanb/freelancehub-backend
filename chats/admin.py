from django.contrib import admin
from .models import Chat

@admin.register(Chat)
class ChatAdmin(admin.ModelAdmin):
    list_display = ('id', 'sender', 'recipient', 'created_at', 'job', 'contract')
    search_fields = ('sender__username', 'recipient__username', 'content')
    list_filter = ('created_at',)