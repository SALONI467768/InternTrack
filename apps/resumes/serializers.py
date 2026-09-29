from rest_framework import serializers
from .models import Resume, ResumeSkill
from apps.skills.models import Skill

class ResumeSkillSerializer(serializers.ModelSerializer):
    skill_name = serializers.CharField(source='skill.name', read_only=True)
    category = serializers.CharField(source='skill.category', read_only=True)

    class Meta:
        model = ResumeSkill
        fields = ('id', 'skill', 'skill_name', 'category', 'frequency', 'context')

class ResumeListSerializer(serializers.ModelSerializer):
    skills_count = serializers.IntegerField(source='resume_skills.count', read_only=True)

    class Meta:
        model = Resume
        fields = (
            'id', 'file_name', 'file_size', 'is_primary', 'match_score',
            'score_breakdown', 'skills_count', 'created_at', 'updated_at'
        )

class ResumeDetailSerializer(serializers.ModelSerializer):
    resume_skills = ResumeSkillSerializer(many=True, read_only=True)
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = Resume
        fields = (
            'id', 'file', 'file_url', 'file_name', 'file_size', 'is_primary',
            'raw_text', 'match_score', 'score_breakdown', 'extracted_data',
            'improvement_suggestions', 'resume_skills', 'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'raw_text', 'match_score', 'score_breakdown', 'extracted_data', 'created_at', 'updated_at')

    def get_file_url(self, obj):
        request = self.context.get('request')
        if obj.file and hasattr(obj.file, 'url'):
            return request.build_absolute_uri(obj.file.url) if request else obj.file.url
        return None

class ResumeUploadSerializer(serializers.ModelSerializer):
    file = serializers.FileField(required=True)
    is_primary = serializers.BooleanField(default=True)

    class Meta:
        model = Resume
        fields = ('file', 'is_primary')

    def validate_file(self, value):
        from django.conf import settings
        max_size = getattr(settings, 'MAX_UPLOAD_SIZE', 10 * 1024 * 1024)
        if value.size > max_size:
            raise serializers.ValidationError(f"File size exceeds limit of {max_size / (1024*1024):.0f}MB.")

        allowed_exts = getattr(settings, 'ALLOWED_RESUME_EXTENSIONS', ['.pdf', '.docx', '.txt'])
        name = value.name.lower()
        if not any(name.endswith(ext) for ext in allowed_exts):
            raise serializers.ValidationError(f"Only {', '.join(allowed_exts)} formats are supported.")

        return value
