import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from apps.skills.models import Skill, UserSkill
from apps.jobs.models import Job, JobSkill
from apps.applications.models import Application

User = get_user_model()

@pytest.mark.django_db
class TestAnalyticsAndSkills:
    def setup_method(self):
        self.client = APIClient()
        self.user = User.objects.create_user(email='analyst@interntrack.ai', password='Password@123')
        self.client.force_authenticate(user=self.user)

        # Setup skills
        self.python_skill = Skill.objects.create(name='Python', category='LANGUAGES')
        self.django_skill = Skill.objects.create(name='Django', category='FRAMEWORKS')
        self.docker_skill = Skill.objects.create(name='Docker', category='DEVOPS')

        # Attach Python to user
        UserSkill.objects.create(user=self.user, skill=self.python_skill, proficiency='ADVANCED')

        # Setup job
        job = Job.objects.create(user=self.user, company='TechCo', title='Backend Eng', raw_description='Python and Django')
        JobSkill.objects.create(job=job, skill=self.python_skill, is_critical=True)
        JobSkill.objects.create(job=job, skill=self.django_skill, is_critical=True)

        Application.objects.create(user=self.user, job=job, status='APPLIED')

    def test_skill_intelligence_endpoint(self):
        res = self.client.get('/api/skills/intelligence/')
        assert res.status_code == 200
        assert 'coverage_percentage' in res.data
        assert 'most_requested_skills' in res.data
        assert res.data['total_tracked_jobs'] == 1

    def test_skill_gap_analysis(self):
        res = self.client.get('/api/skills/gap-analysis/')
        assert res.status_code == 200
        assert 'critical_gaps' in res.data
        assert 'matched_skills' in res.data
        
        # Django should be identified in critical gaps because user doesn't have it
        crit_names = [g['skill'] for g in res.data['critical_gaps']]
        assert 'Django' in crit_names

        # Python should be matched
        match_names = [m['skill'] for m in res.data['matched_skills']]
        assert 'Python' in match_names

    def test_dashboard_analytics_kpi(self):
        res = self.client.get('/api/analytics/dashboard/')
        assert res.status_code == 200
        kpis = res.data['kpis']
        assert kpis['total_applications'] == 1
        assert kpis['active_applications'] == 1
        assert 'formulas' in res.data
        assert 'charts' in res.data
