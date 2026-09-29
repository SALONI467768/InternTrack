import pytest
from services.ai.nlp_fallback_provider import LocalNLPFallbackProvider

class TestAIServiceLayer:
    def setup_method(self):
        self.provider = LocalNLPFallbackProvider()

    def test_resume_parser_fallback(self):
        sample_resume = """
        Alex Morgan
        alex@university.edu | (555) 123-4567
        
        Education:
        B.S. in Computer Science, 2026
        
        Skills:
        Python, Django, PostgreSQL, Docker, Git, SQL, REST API
        
        Projects:
        Task Management API built using Django REST Framework and PostgreSQL.
        Implemented JWT authentication and Docker containerization.
        """
        analysis = self.provider.parse_resume(sample_resume)
        
        assert analysis['full_name'] == 'Alex Morgan'
        assert analysis['email'] == 'alex@university.edu'
        assert 'Python' in analysis['detected_skills']
        assert 'PostgreSQL' in analysis['detected_skills']
        assert analysis['match_score'] > 60
        assert 'score_breakdown' in analysis
        assert len(analysis['improvement_suggestions']) > 0

    def test_job_match_analyzer_fallback(self):
        profile_data = {
            'skills': ['Python', 'SQL', 'Git', 'Flask'],
            'target_role': 'Python Developer'
        }
        resume_data = {
            'detected_skills': ['Python', 'SQL', 'Git']
        }
        job_data = {
            'title': 'Django Backend Engineer',
            'required_skills': ['Python', 'Django', 'PostgreSQL'],
            'preferred_skills': ['Docker']
        }

        match_res = self.provider.match_profile_and_resume_to_job(profile_data, resume_data, job_data)
        
        assert 'Python' in match_res['matched_skills']
        # Flask should be recognized as related to Django
        related_targets = [r['job_skill'] for r in match_res['related_skills']]
        assert 'Django' in related_targets
        assert match_res['job_match_score'] > 0
        assert 'disclaimer' in match_res
        assert 'checklist' in match_res
