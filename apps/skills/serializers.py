from rest_framework import serializers
from .models import Skill, UserSkill

class SkillSerializer(serializers.ModelSerializer):
    category_display = serializers.CharField(source='get_category_display', read_only=True)

    class Meta:
        model = Skill
        fields = ('id', 'name', 'slug', 'category', 'category_display', 'aliases', 'description')

class UserSkillSerializer(serializers.ModelSerializer):
    skill_name = serializers.CharField(source='skill.name', read_only=True)
    category = serializers.CharField(source='skill.category', read_only=True)
    category_display = serializers.CharField(source='skill.get_category_display', read_only=True)
    proficiency_display = serializers.CharField(source='get_proficiency_display', read_only=True)

    class Meta:
        model = UserSkill
        fields = (
            'id', 'skill', 'skill_name', 'category', 'category_display',
            'proficiency', 'proficiency_display', 'years_of_experience', 'created_at'
        )
        read_only_fields = ('id', 'created_at')

    def create(self, validated_data):
        user = self.context['request'].user
        skill = validated_data['skill']
        user_skill, created = UserSkill.objects.update_or_create(
            user=user,
            skill=skill,
            defaults={
                'proficiency': validated_data.get('proficiency', 'INTERMEDIATE'),
                'years_of_experience': validated_data.get('years_of_experience', 1.0)
            }
        )
        # Update user profile completion
        if hasattr(user, 'profile'):
            user.profile.calculate_completion()
            user.profile.save()
        return user_skill
