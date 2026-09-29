from rest_framework import serializers
from .models import Application, ApplicationStatusHistory, FollowUp
from apps.jobs.serializers import JobListSerializer, JobDetailSerializer

class ApplicationStatusHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ApplicationStatusHistory
        fields = ('id', 'from_status', 'to_status', 'changed_at', 'notes')

class FollowUpSerializer(serializers.ModelSerializer):
    company = serializers.CharField(source='application.job.company', read_only=True)
    job_title = serializers.CharField(source='application.job.title', read_only=True)

    class Meta:
        model = FollowUp
        fields = ('id', 'application', 'company', 'job_title', 'follow_up_date', 'is_completed', 'notes', 'created_at')
        read_only_fields = ('id', 'created_at')

class ApplicationListSerializer(serializers.ModelSerializer):
    company = serializers.CharField(source='job.company', read_only=True)
    job_title = serializers.CharField(source='job.title', read_only=True)
    location = serializers.CharField(source='job.location', read_only=True)
    employment_type = serializers.CharField(source='job.employment_type', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Application
        fields = (
            'id', 'job', 'company', 'job_title', 'location', 'employment_type',
            'status', 'status_display', 'applied_date', 'deadline',
            'salary_stipend', 'source', 'match_score_at_application', 'created_at', 'updated_at'
        )

class ApplicationDetailSerializer(serializers.ModelSerializer):
    job_details = JobDetailSerializer(source='job', read_only=True)
    history = ApplicationStatusHistorySerializer(many=True, read_only=True)
    follow_ups = FollowUpSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Application
        fields = (
            'id', 'job', 'job_details', 'status', 'status_display',
            'applied_date', 'deadline', 'salary_stipend', 'source',
            'notes', 'match_score_at_application', 'history', 'follow_ups',
            'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'history', 'created_at', 'updated_at')

class ApplicationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Application
        fields = ('job', 'status', 'applied_date', 'deadline', 'salary_stipend', 'source', 'notes')

class ApplicationStatusUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=Application.STATUS_CHOICES)
    notes = serializers.CharField(required=False, allow_blank=True, default='')
