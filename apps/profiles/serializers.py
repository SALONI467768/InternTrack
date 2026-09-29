from rest_framework import serializers
from .models import Profile
from apps.skills.models import UserSkill

class UserSkillInlineSerializer(serializers.ModelSerializer):
    skill_name = serializers.CharField(source='skill.name', read_only=True)
    category = serializers.CharField(source='skill.category', read_only=True)

    class Meta:
        model = UserSkill
        fields = ('id', 'skill', 'skill_name', 'category', 'proficiency', 'years_of_experience')

class ProfileSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='user.email', read_only=True)
    skills = UserSkillInlineSerializer(source='user.user_skills', many=True, read_only=True)
    completion_percentage = serializers.IntegerField(read_only=True)

    class Meta:
        model = Profile
        fields = (
            'id', 'email', 'full_name', 'phone', 'location', 'bio', 'target_role',
            'college', 'degree', 'graduation_year',
            'github_url', 'linkedin_url', 'portfolio_url',
            'preferred_roles', 'preferred_locations', 'work_mode_preference', 'expected_salary',
            'projects', 'experience', 'certifications',
            'completion_percentage', 'skills', 'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'completion_percentage', 'created_at', 'updated_at')
