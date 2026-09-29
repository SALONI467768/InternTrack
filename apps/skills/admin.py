from django.contrib import admin
from .models import Skill, UserSkill

@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'slug', 'created_at')
    list_filter = ('category',)
    search_fields = ('name', 'aliases')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(UserSkill)
class UserSkillAdmin(admin.ModelAdmin):
    list_display = ('user', 'skill', 'proficiency', 'years_of_experience', 'created_at')
    list_filter = ('proficiency', 'skill__category')
    search_fields = ('user__email', 'skill__name')
