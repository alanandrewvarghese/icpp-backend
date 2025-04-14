from django.contrib import admin
from .models import CompletionStatus

@admin.register(CompletionStatus)
class CompletionStatusAdmin(admin.ModelAdmin):
    list_display = ['user', 'content_type', 'content_id', 'completed', 'completed_at']
    list_filter = ['content_type', 'completed']
    search_fields = ['user__username', 'content_id']
    date_hierarchy = 'completed_at'
