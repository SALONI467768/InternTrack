import uuid
from django.db import models
from django.conf import settings
from apps.jobs.models import Job

class Application(models.Model):
    """
    Main job/internship application record tracking status, timeline, and dates.
    """
    STATUS_CHOICES = (
        ('SAVED', 'Saved / Bookmarked'),
        ('APPLIED', 'Applied'),
        ('ASSESSMENT', 'Online Assessment / Screening'),
        ('INTERVIEW', 'Interviewing'),
        ('OFFER', 'Offer Received'),
        ('REJECTED', 'Rejected'),
        ('WITHDRAWN', 'Withdrawn'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='applications')
    job = models.OneToOneField(Job, on_delete=models.CASCADE, related_name='application')
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='SAVED', db_index=True)
    applied_date = models.DateField(null=True, blank=True)
    deadline = models.DateField(null=True, blank=True)
    salary_stipend = models.CharField(max_length=100, blank=True, default='')
    source = models.CharField(max_length=100, blank=True, default='LinkedIn')
    notes = models.TextField(blank=True, default='')
    match_score_at_application = models.FloatField(default=0.0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        verbose_name = 'Application'
        verbose_name_plural = 'Applications'

    def __str__(self):
        return f"{self.user.email} -> {self.job.title} at {self.job.company} [{self.get_status_display()}]"

    def update_status(self, new_status, notes=""):
        """Updates status and creates a status transition record."""
        old_status = self.status
        if old_status != new_status:
            self.status = new_status
            self.save()
            ApplicationStatusHistory.objects.create(
                application=self,
                from_status=old_status,
                to_status=new_status,
                notes=notes
            )

class ApplicationStatusHistory(models.Model):
    """
    Historical log of application stage transitions.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name='history')
    from_status = models.CharField(max_length=20)
    to_status = models.CharField(max_length=20)
    changed_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, default='')

    class Meta:
        ordering = ['changed_at']
        verbose_name = 'Application Status History'
        verbose_name_plural = 'Application Status Histories'

    def __str__(self):
        return f"{self.application.job.company}: {self.from_status} -> {self.to_status}"

class FollowUp(models.Model):
    """
    User-scheduled follow-up dates and reminders.
    External communication is strictly triggered by the user.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='follow_ups')
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name='follow_ups')
    follow_up_date = models.DateField(db_index=True)
    is_completed = models.BooleanField(default=False)
    notes = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['follow_up_date']
        verbose_name = 'Follow Up'
        verbose_name_plural = 'Follow Ups'

    def __str__(self):
        return f"Follow up for {self.application.job.company} on {self.follow_up_date}"
