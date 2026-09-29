import uuid
from django.db import models
from django.conf import settings
from apps.applications.models import Application

class Interview(models.Model):
    """
    Candidate interview event tied to an application.
    """
    ROUND_CHOICES = (
        ('HR', 'HR / Recruiter Screening'),
        ('TECHNICAL', 'Technical Round 1'),
        ('CODING', 'Live Coding / DSA'),
        ('MANAGERIAL', 'Managerial / Team Fit'),
        ('FINAL', 'Final Round / Leadership'),
    )

    TYPE_CHOICES = (
        ('VIDEO', 'Video Call (Google Meet, Zoom, Teams)'),
        ('PHONE', 'Phone Call'),
        ('ONSITE', 'On-site / In-person'),
        ('ASYNC', 'Recorded / Automated (HireVue, etc.)'),
    )

    RESULT_CHOICES = (
        ('SCHEDULED', 'Upcoming / Scheduled'),
        ('COMPLETED', 'Completed / Awaiting Feedback'),
        ('PASSED', 'Passed (Advancing)'),
        ('FAILED', 'Did Not Pass'),
        ('CANCELLED', 'Cancelled / Rescheduled'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='interviews')
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name='interviews')
    
    round_type = models.CharField(max_length=20, choices=ROUND_CHOICES, default='TECHNICAL')
    interview_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='VIDEO')
    scheduled_at = models.DateTimeField(db_index=True)
    meeting_link = models.URLField(blank=True, default='')
    
    questions_asked = models.TextField(blank=True, default='', help_text="Questions asked during the actual interview")
    feedback = models.TextField(blank=True, default='', help_text="Interviewer feedback or self-reflection notes")
    result = models.CharField(max_length=20, choices=RESULT_CHOICES, default='SCHEDULED')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['scheduled_at']
        verbose_name = 'Interview'
        verbose_name_plural = 'Interviews'

    def __str__(self):
        return f"{self.application.job.company} - {self.get_round_type_display()} on {self.scheduled_at.strftime('%Y-%m-%d')}"

class InterviewQuestion(models.Model):
    """
    Practice interview questions catalog categorized by technology and topic.
    """
    QUESTION_TYPES = (
        ('TECHNICAL', 'Technical Concepts'),
        ('CODING', 'Coding & DSA'),
        ('HR', 'HR & Behavioral (STAR)'),
        ('SQL', 'SQL Queries & Optimization'),
        ('PROJECT', 'Project & Architecture Deep Dive'),
    )

    DIFFICULTY_CHOICES = (
        ('EASY', 'Easy'),
        ('MEDIUM', 'Medium'),
        ('HARD', 'Hard'),
    )

    category = models.CharField(max_length=50, db_index=True, help_text="e.g. Python, Django, SQL, REST API, Git, Docker")
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPES, default='TECHNICAL')
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES, default='MEDIUM')
    question_text = models.TextField()
    model_answer = models.TextField()
    explanation = models.TextField(blank=True, default='')

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['category', 'difficulty']
        verbose_name = 'Interview Question'
        verbose_name_plural = 'Interview Questions'

    def __str__(self):
        return f"[{self.category}] {self.question_text[:60]}..."

class InterviewAttempt(models.Model):
    """
    Records candidate practice responses and automated self-evaluation scores.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='interview_attempts')
    question = models.ForeignKey(InterviewQuestion, on_delete=models.CASCADE, related_name='attempts')
    user_answer = models.TextField()
    score = models.FloatField(default=0.0, help_text="Score 0-100")
    feedback = models.TextField(blank=True, default='')
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-submitted_at']
        verbose_name = 'Interview Attempt'
        verbose_name_plural = 'Interview Attempts'

    def __str__(self):
        return f"{self.user.email} - {self.question.category} (Score: {self.score})"
