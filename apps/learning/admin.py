from django.contrib import admin
from .models import LearningRoadmap, LearningTask

class LearningTaskInline(admin.TabularInline):
    model = LearningTask
    extra = 0

@admin.register(LearningRoadmap)
class LearningRoadmapAdmin(admin.ModelAdmin):
    list_display = ('user', 'target_role', 'progress_percentage', 'created_at')
    inlines = [LearningTaskInline]

@admin.register(LearningTask)
class LearningTaskAdmin(admin.ModelAdmin):
    list_display = ('roadmap', 'week_number', 'topic', 'priority', 'status', 'estimated_hours')
    list_filter = ('priority', 'status', 'week_number')
    search_fields = ('topic', 'description', 'practice_task')
