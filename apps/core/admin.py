from django.contrib import admin
from .models import ActivityLog

@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'action', 'details', 'created_at')
    list_filter = ('action', 'created_at')
    search_fields = ('user__email', 'action', 'details')
    readonly_fields = ('user', 'action', 'details', 'metadata', 'created_at')
