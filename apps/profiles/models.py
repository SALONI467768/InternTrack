import uuid
from django.db import models
from django.conf import settings

class Profile(models.Model):
    """
    Candidate & Student Profile model storing portfolio, preferences, education,
    and dynamically tracking profile completion percentage.
    """
    WORK_MODE_CHOICES = (
        ('REMOTE', 'Remote Only'),
        ('HYBRID', 'Hybrid'),
        ('ONSITE', 'On-site'),
        ('FLEXIBLE', 'Flexible / Any'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    
    # Personal Info
    full_name = models.CharField(max_length=200, blank=True, default='')
    phone = models.CharField(max_length=30, blank=True, default='')
    location = models.CharField(max_length=150, blank=True, default='')
    bio = models.TextField(blank=True, default='')
    target_role = models.CharField(max_length=150, blank=True, default='Full Stack Developer')

    # Education
    college = models.CharField(max_length=255, blank=True, default='')
    degree = models.CharField(max_length=150, blank=True, default='')
    graduation_year = models.IntegerField(null=True, blank=True)

    # Social & Links
    github_url = models.URLField(blank=True, default='')
    linkedin_url = models.URLField(blank=True, default='')
    portfolio_url = models.URLField(blank=True, default='')

    # Preferences
    preferred_roles = models.JSONField(default=list, blank=True)
    preferred_locations = models.JSONField(default=list, blank=True)
    work_mode_preference = models.CharField(max_length=20, choices=WORK_MODE_CHOICES, default='FLEXIBLE')
    expected_salary = models.CharField(max_length=100, blank=True, default='')

    # Structured Data
    projects = models.JSONField(default=list, blank=True)
    experience = models.JSONField(default=list, blank=True)
    certifications = models.JSONField(default=list, blank=True)

    # Completion cache
    completion_percentage = models.PositiveSmallIntegerField(default=20)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'

    def __str__(self):
        return f"Profile of {self.user.email} ({self.full_name or 'Unnamed'})"

    def calculate_completion(self):
        """
        Calculates dynamic profile completion percentage (0-100%).
        Weights:
        - Full Name & Contact (15%)
        - College & Degree (15%)
        - Target Role & Preferences (15%)
        - Social Links (GitHub / LinkedIn) (15%)
        - Skills added (20%)
        - Projects or Experience (20%)
        """
        score = 0
        if self.full_name and self.phone:
            score += 15
        elif self.full_name or self.phone:
            score += 8

        if self.college and self.degree:
            score += 15
        elif self.college or self.degree:
            score += 8

        if self.target_role:
            score += 15

        if self.github_url or self.linkedin_url or self.portfolio_url:
            score += 15

        # Check skills
        user_skills_count = self.user.user_skills.count() if hasattr(self.user, 'user_skills') else 0
        if user_skills_count >= 5:
            score += 20
        elif user_skills_count > 0:
            score += 10

        # Check projects or experience
        if bool(self.projects) or bool(self.experience):
            score += 20

        self.completion_percentage = min(score, 100)
        return self.completion_percentage

    def save(self, *args, **kwargs):
        # Calculate completion before saving if user has PK
        if self.user_id:
            try:
                self.calculate_completion()
            except Exception:
                pass
        super().save(*args, **kwargs)
