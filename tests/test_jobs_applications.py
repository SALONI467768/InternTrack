import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from apps.jobs.models import Job, JobSkill
from apps.applications.models import Application
from apps.skills.models import Skill

User = get_user_model()

@pytest.mark.django_db
class TestJobsAndApplications:
    def setup_method(self):
        self.client = APIClient()
        self.user = User.objects.create_user(email='test_dev@interntrack.ai', password='Password@123')
        self.client.force_authenticate(user=self.user)

    def test_job_parse_and_create(self):
        raw_text = """
        About Us: Acme Corp is looking for a Python Backend Developer Intern.
        Requirements:
        - Strong proficiency in Python, Django, and SQL.
        - Experience building REST API services.
        - Familiarity with Docker and Git.
        Responsibilities:
        - Design scalable API endpoints.
        - Optimize database query performance.
        """
        response = self.client.post('/api/jobs/parse-and-create/', {
            'raw_text': raw_text,
            'company': 'Acme Corp',
            'title': 'Python Backend Developer Intern'
        })
        assert response.status_code == 201
        assert response.data['company'] == 'Acme Corp'
        assert response.data['title'] == 'Python Backend Developer Intern'
        
        # Check job in DB
        job = Job.objects.get(id=response.data['id'])
        assert job.job_skills.count() >= 3

        # Check Application was automatically tracked
        assert Application.objects.filter(job=job, user=self.user).exists()

    def test_application_status_transition(self):
        job = Job.objects.create(
            user=self.user,
            company='Starlight AI',
            title='Software Engineer',
            raw_description='Python and SQL required.'
        )
        app = Application.objects.create(
            user=self.user,
            job=job,
            status='SAVED'
        )

        # Transition SAVED -> APPLIED
        res = self.client.post(f'/api/applications/{app.id}/update-status/', {
            'status': 'APPLIED',
            'notes': 'Applied via LinkedIn with tailored resume'
        })
        assert res.status_code == 200
        app.refresh_from_db()
        assert app.status == 'APPLIED'
        assert app.history.count() == 1
        assert app.history.first().to_status == 'APPLIED'

        # Transition APPLIED -> INTERVIEW
        res2 = self.client.post(f'/api/applications/{app.id}/update-status/', {
            'status': 'INTERVIEW',
            'notes': 'Recruiter reached out for technical interview'
        })
        assert res2.status_code == 200
        app.refresh_from_db()
        assert app.status == 'INTERVIEW'
        assert app.history.count() == 2
