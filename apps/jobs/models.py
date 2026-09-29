import uuid
from django.db import models
from django.conf import settings
from apps.skills.models import Skill

class Job(models.Model):
    """
    Job Requirement entity containing structured extracted metadata,
    skills demanded, and requirements.
    """
    EMPLOYMENT_TYPES = (
        ('INTERNSHIP', 'Internship'),
        ('FULL_TIME', 'Full-time'),
        ('PART_TIME', 'Part-time'),
        ('CONTRACT', 'Contract / Project'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='tracked_jobs')
    
    company = models.CharField(max_length=200, db_index=True)
    title = models.CharField(max_length=200, db_index=True)
    job_url = models.URLField(blank=True, default='')
    location = models.CharField(max_length=150, default='Remote / Flexible')
    employment_type = models.CharField(max_length=20, choices=EMPLOYMENT_TYPES, default='INTERNSHIP')
    
    experience_level = models.CharField(max_length=100, blank=True, default='Fresher / 0-1 Years')
    education_requirement = models.CharField(max_length=255, blank=True, default='')
    salary_range = models.CharField(max_length=100, blank=True, default='')
    
    raw_description = models.TextField(help_text="Full original job description text")
    parsed_requirements = models.JSONField(
        default=dict,
        blank=True,
        help_text="Structured requirements: responsibilities, requirements, preferred criteria"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Job'
        verbose_name_plural = 'Jobs'

    def __str__(self):
        return f"{self.title} at {self.company}"

class JobSkill(models.Model):
    """
    Required or preferred skill linked to a specific job requirement.
    """
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='job_skills')
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE, related_name='job_demands')
    is_critical = models.BooleanField(default=True, help_text="True if mandatory/critical, False if nice-to-have")

    class Meta:
        unique_together = ('job', 'skill')
        ordering = ['-is_critical', 'skill__name']
        verbose_name = 'Job Skill'
        verbose_name_plural = 'Job Skills'

    def __str__(self):
        status_label = 'Mandatory' if self.is_critical else 'Preferred'
        return f"{self.job.title} - {self.skill.name} ({status_label})"
