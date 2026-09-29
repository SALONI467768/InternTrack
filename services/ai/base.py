from abc import ABC, abstractmethod
from typing import Dict, Any, List

class BaseAIProvider(ABC):
    """
    Abstract Base Class for AI and NLP intelligence providers in InternTrack AI.
    All providers (Gemini, OpenAI, Local NLP) must conform to this interface.
    """

    @abstractmethod
    def parse_resume(self, raw_text: str) -> Dict[str, Any]:
        """
        Parses resume text into structured sections:
        - full_name, email, phone
        - education: list of {degree, college, year}
        - skills: list of detected skill strings
        - projects: list of {title, description, technologies}
        - experience: list of {role, company, duration, responsibilities}
        - certifications: list of strings
        - score_breakdown: {skills, projects, keywords, education, experience}
        - match_score: float (0-100)
        - improvement_suggestions: list of strings
        """
        pass

    @abstractmethod
    def analyze_job_description(self, raw_text: str) -> Dict[str, Any]:
        """
        Extracts structured metadata from a job description:
        - title, company, location, employment_type, experience_level, salary_range
        - required_skills: list of critical skill strings
        - preferred_skills: list of nice-to-have skill strings
        - education_requirements: str
        - responsibilities: list of key responsibility strings
        """
        pass

    @abstractmethod
    def match_profile_and_resume_to_job(
        self,
        profile_data: Dict[str, Any],
        resume_data: Dict[str, Any],
        job_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Evaluates candidate alignment against a specific job requirement:
        - job_match_score: float (0-100)
        - breakdown: {skills: float, experience: float, education: float, keywords: float}
        - matched_skills: list of strings
        - missing_skills: list of strings
        - related_skills: list of {user_skill: str, job_skill: str, rationale: str}
        - interview_checklist: list of preparation topics
        - summary_rationale: str
        """
        pass

    @abstractmethod
    def generate_career_insights(
        self,
        user_data: Dict[str, Any],
        tracked_jobs: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Generates actionable, fact-grounded career observations and recommendations.
        """
        pass

    @abstractmethod
    def generate_interview_questions(
        self,
        job_data: Dict[str, Any],
        skills: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Generates targeted practice interview questions (Technical, Coding, HR, Project, SQL)
        with model answers and explanations.
        """
        pass

    @abstractmethod
    def generate_cover_letter(
        self,
        user_profile: Dict[str, Any],
        job_data: Dict[str, Any]
    ) -> str:
        """
        Generates an editable, tailored cover letter draft.
        """
        pass
