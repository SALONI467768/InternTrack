import uuid
from django.db import models
from django.conf import settings
from apps.skills.models import Skill

class LearningRoadmap(models.Model):
    """
    Candidate learning plan dynamically generated to bridge identified skill gaps.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='roadmaps')
    target_role = models.CharField(max_length=150, default='Full Stack Python Developer')
    progress_percentage = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Learning Roadmap'
        verbose_name_plural = 'Learning Roadmaps'

    def __str__(self):
        return f"{self.user.email} - {self.target_role} ({self.progress_percentage}%)"

    def recalculate_progress(self):
        """Calculates completed tasks vs total tasks."""
        total = self.tasks.count()
        if total == 0:
            self.progress_percentage = 0
        else:
            completed = self.tasks.filter(status='COMPLETED').count()
            self.progress_percentage = int((completed / total) * 100)
        self.save(update_fields=['progress_percentage', 'updated_at'])
        return self.progress_percentage

class LearningTask(models.Model):
    """
    Individual learning milestone with estimated effort and a concrete practice task.
    """
    PRIORITY_CHOICES = (
        ('CRITICAL', 'Critical (Must-Have for Role)'),
        ('IMPORTANT', 'Important (Competitive Advantage)'),
        ('OPTIONAL', 'Optional (Nice-to-Have)'),
    )

    STATUS_CHOICES = (
        ('NOT_STARTED', 'Not Started'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    roadmap = models.ForeignKey(LearningRoadmap, on_delete=models.CASCADE, related_name='tasks')
    skill = models.ForeignKey(Skill, on_delete=models.SET_NULL, null=True, blank=True, related_name='learning_tasks')
    
    week_number = models.PositiveSmallIntegerField(default=1)
    topic = models.CharField(max_length=200)
    description = models.TextField()
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='CRITICAL')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='NOT_STARTED')
    estimated_hours = models.FloatField(default=6.0)
    practice_task = models.TextField(help_text="Hands-on mini-project or coding task to solidify concept")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['week_number', 'priority']
        verbose_name = 'Learning Task'
        verbose_name_plural = 'Learning Tasks'

    def __str__(self):
        return f"Week {self.week_number}: {self.topic} [{self.status}]"
