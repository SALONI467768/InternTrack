from django.contrib import admin
from .models import Job, JobSkill

class JobSkillInline(admin.TabularInline):
    model = JobSkill
    extra = 0

@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ('title', 'company', 'location', 'employment_type', 'user', 'created_at')
    list_filter = ('employment_type', 'created_at')
    search_fields = ('title', 'company', 'raw_description')
    inlines = [JobSkillInline]
