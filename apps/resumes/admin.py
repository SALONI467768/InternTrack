from django.contrib import admin
from .models import Resume, ResumeSkill

class ResumeSkillInline(admin.TabularInline):
    model = ResumeSkill
    extra = 0

@admin.register(Resume)
class ResumeAdmin(admin.ModelAdmin):
    list_display = ('user', 'file_name', 'is_primary', 'match_score', 'file_size', 'created_at')
    list_filter = ('is_primary',)
    search_fields = ('user__email', 'file_name')
    inlines = [ResumeSkillInline]
    readonly_fields = ('match_score', 'score_breakdown', 'extracted_data', 'created_at', 'updated_at')
