import uuid
from django.db import models
from django.conf import settings

class Skill(models.Model):
    """
    Standardized skill entity supporting categorization, aliases for robust matching,
    and market frequency tracking.
    """
    CATEGORY_CHOICES = (
        ('LANGUAGES', 'Programming Languages'),
        ('FRAMEWORKS', 'Web & App Frameworks'),
        ('DATABASES', 'Databases & Storage'),
        ('DEVOPS', 'DevOps & Infrastructure'),
        ('CLOUD', 'Cloud Platforms'),
        ('FUNDAMENTALS', 'CS Fundamentals & Architecture'),
        ('TESTING', 'Testing & QA'),
        ('TOOLS', 'Developer Tools & VCS'),
        ('SOFT_SKILLS', 'Soft Skills & Leadership'),
    )

    name = models.CharField(max_length=100, unique=True, db_index=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default='LANGUAGES')
    aliases = models.JSONField(default=list, blank=True, help_text="Alternative names, acronyms, or syntax")
    description = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Skill'
        verbose_name_plural = 'Skills'

    def __str__(self):
        return f"{self.name} ({self.get_category_display()})"

    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

class UserSkill(models.Model):
    """
    Links a user with a specific skill and records their self-assessed proficiency.
    """
    PROFICIENCY_CHOICES = (
        ('BEGINNER', 'Beginner (Academic / Learning)'),
        ('INTERMEDIATE', 'Intermediate (Built Projects)'),
        ('ADVANCED', 'Advanced (Production Experience)'),
        ('EXPERT', 'Expert (Mastery / Architecture)'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='user_skills')
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE, related_name='user_instances')
    proficiency = models.CharField(max_length=20, choices=PROFICIENCY_CHOICES, default='INTERMEDIATE')
    years_of_experience = models.FloatField(default=1.0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'skill')
        ordering = ['skill__name']
        verbose_name = 'User Skill'
        verbose_name_plural = 'User Skills'

    def __str__(self):
        return f"{self.user.email} - {self.skill.name} ({self.proficiency})"
