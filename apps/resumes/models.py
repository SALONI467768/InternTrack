import uuid
from django.db import models
from django.conf import settings
from apps.skills.models import Skill

def resume_upload_path(instance, filename):
    return f"resumes/{instance.user.id}/{uuid.uuid4().hex}_{filename}"

class Resume(models.Model):
    """
    Resume file and extracted ATS/skills analytics.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='resumes')
    file = models.FileField(upload_to=resume_upload_path)
    file_name = models.CharField(max_length=255)
    file_size = models.PositiveIntegerField(default=0, help_text="Size in bytes")
    raw_text = models.TextField(blank=True, default='')
    is_primary = models.BooleanField(default=False)

    # Scoring & Breakdown
    match_score = models.FloatField(default=0.0, help_text="InternTrack Resume Match Score (0-100)")
    score_breakdown = models.JSONField(
        default=dict,
        help_text="Component breakdown: skills, projects, keywords, education, experience"
    )
    extracted_data = models.JSONField(
        default=dict,
        help_text="Extracted structured sections: contact, education, skills, projects, experience, certifications"
    )
    improvement_suggestions = models.JSONField(
        default=list,
        help_text="Actionable suggestions to improve resume impact"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_primary', '-created_at']
        verbose_name = 'Resume'
        verbose_name_plural = 'Resumes'

    def __str__(self):
        return f"{self.user.email} - {self.file_name} (Score: {self.match_score})"

    def save(self, *args, **kwargs):
        if self.is_primary:
            # Set other resumes of the user to non-primary
            Resume.objects.filter(user=self.user, is_primary=True).exclude(pk=self.pk).update(is_primary=False)
        super().save(*args, **kwargs)

class ResumeSkill(models.Model):
    """
    Skills detected specifically within this resume document.
    """
    resume = models.ForeignKey(Resume, on_delete=models.CASCADE, related_name='resume_skills')
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE, related_name='resume_instances')
    frequency = models.PositiveIntegerField(default=1)
    context = models.CharField(max_length=255, blank=True, default='')

    class Meta:
        unique_together = ('resume', 'skill')
        ordering = ['-frequency']
        verbose_name = 'Resume Skill'
        verbose_name_plural = 'Resume Skills'

    def __str__(self):
        return f"{self.resume.file_name} - {self.skill.name} (x{self.frequency})"
