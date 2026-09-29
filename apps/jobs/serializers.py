from rest_framework import serializers
from .models import Job, JobSkill
from apps.skills.models import Skill

class JobSkillSerializer(serializers.ModelSerializer):
    skill_name = serializers.CharField(source='skill.name', read_only=True)
    category = serializers.CharField(source='skill.category', read_only=True)

    class Meta:
        model = JobSkill
        fields = ('id', 'skill', 'skill_name', 'category', 'is_critical')

class JobListSerializer(serializers.ModelSerializer):
    skills = serializers.SerializerMethodField()
    application_id = serializers.SerializerMethodField()
    application_status = serializers.SerializerMethodField()

    class Meta:
        model = Job
        fields = (
            'id', 'company', 'title', 'location', 'employment_type',
            'experience_level', 'salary_range', 'skills',
            'application_id', 'application_status', 'created_at'
        )

    def get_skills(self, obj):
        return [js.skill.name for js in obj.job_skills.select_related('skill')[:5]]

    def get_application_id(self, obj):
        app = getattr(obj, 'application', None)
        return app.id if app else None

    def get_application_status(self, obj):
        app = getattr(obj, 'application', None)
        return app.status if app else None

class JobDetailSerializer(serializers.ModelSerializer):
    job_skills = JobSkillSerializer(many=True, read_only=True)

    class Meta:
        model = Job
        fields = (
            'id', 'company', 'title', 'job_url', 'location', 'employment_type',
            'experience_level', 'education_requirement', 'salary_range',
            'raw_description', 'parsed_requirements', 'job_skills', 'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'created_at', 'updated_at')

class JobCreateFromTextSerializer(serializers.Serializer):
    raw_text = serializers.CharField(required=True, help_text="Paste raw job description")
    company = serializers.CharField(required=False, allow_blank=True)
    title = serializers.CharField(required=False, allow_blank=True)
    job_url = serializers.URLField(required=False, allow_blank=True)
    location = serializers.CharField(required=False, allow_blank=True)
    employment_type = serializers.CharField(required=False, default='INTERNSHIP')
