from django.contrib import admin
from .models import Profile

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'full_name', 'target_role', 'college', 'degree', 'completion_percentage', 'updated_at')
    search_fields = ('user__email', 'full_name', 'college', 'target_role')
    list_filter = ('work_mode_preference', 'graduation_year')
    readonly_fields = ('completion_percentage', 'created_at', 'updated_at')
