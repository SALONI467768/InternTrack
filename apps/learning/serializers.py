from rest_framework import serializers
from .models import LearningRoadmap, LearningTask

class LearningTaskSerializer(serializers.ModelSerializer):
    skill_name = serializers.CharField(source='skill.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)

    class Meta:
        model = LearningTask
        fields = (
            'id', 'roadmap', 'skill', 'skill_name', 'week_number',
            'topic', 'description', 'priority', 'priority_display',
            'status', 'status_display', 'estimated_hours', 'practice_task',
            'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'created_at', 'updated_at')

class LearningRoadmapSerializer(serializers.ModelSerializer):
    tasks = LearningTaskSerializer(many=True, read_only=True)
    total_tasks = serializers.IntegerField(source='tasks.count', read_only=True)
    completed_tasks = serializers.SerializerMethodField()

    class Meta:
        model = LearningRoadmap
        fields = (
            'id', 'target_role', 'progress_percentage', 'total_tasks',
            'completed_tasks', 'tasks', 'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'progress_percentage', 'created_at', 'updated_at')

    def get_completed_tasks(self, obj):
        return obj.tasks.filter(status='COMPLETED').count()
