import uuid
from django.db import models
from django.conf import settings

class ActivityLog(models.Model):
    """
    Audit log recording critical user actions and system events.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='activity_logs')
    action = models.CharField(max_length=100, db_index=True)
    details = models.TextField()
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Activity Log'
        verbose_name_plural = 'Activity Logs'

    def __str__(self):
        return f"[{self.created_at.strftime('%Y-%m-%d %H:%M')}] {self.user.email} - {self.action}"

    @classmethod
    def log_activity(cls, user, action, details, metadata=None):
        """Helper to safely record an activity entry."""
        if not user or not user.is_authenticated:
            return None
        try:
            return cls.objects.create(
                user=user,
                action=action,
                details=details,
                metadata=metadata or {}
            )
        except Exception:
            return None
