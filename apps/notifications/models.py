import uuid
from django.db import models
from django.conf import settings

class Notification(models.Model):
    """
    In-app alert notification entity.
    """
    TYPE_CHOICES = (
        ('INTERVIEW_REMINDER', 'Interview Reminder'),
        ('APPLICATION_DEADLINE', 'Application Deadline'),
        ('FOLLOW_UP_DUE', 'Follow-up Due'),
        ('SKILL_GAP_ALERT', 'Skill Gap Alert'),
        ('PROFILE_INCOMPLETE', 'Profile Incomplete'),
        ('APPLICATION_UPDATE', 'Application Update'),
        ('SYSTEM', 'System Alert'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(max_length=30, choices=TYPE_CHOICES, default='SYSTEM')
    is_read = models.BooleanField(default=False, db_index=True)
    link = models.CharField(max_length=255, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'

    def __str__(self):
        return f"{self.user.email} - {self.title} ({'Read' if self.is_read else 'Unread'})"
