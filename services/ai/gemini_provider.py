import json
import logging
import requests
from typing import Dict, Any, List
from .base import BaseAIProvider
from .nlp_fallback_provider import LocalNLPFallbackProvider

logger = logging.getLogger(__name__)

class GeminiAIProvider(BaseAIProvider):
    """
    Google Gemini AI Provider utilizing the REST API endpoint.
    Extracts deep semantic nuances, custom evaluation, and personalized coaching.
    Falls back gracefully to LocalNLPFallbackProvider on network or quota errors.
    """

    def __init__(self, api_key: str, model: str = "gemini-2.5-flash"):
        self.api_key = api_key
        self.model = model
        self.endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        self.fallback = LocalNLPFallbackProvider()

    def _call_gemini(self, prompt: str, system_instruction: str = "") -> str:
        """Helper to invoke Gemini API with clean error handling."""
        payload = {
            "contents": [
                {
                    "parts": [{"text": prompt}]
                }
            ],
            "generationConfig": {
                "temperature": 0.2,
                "responseMimeType": "application/json"
            }
        }
        if system_instruction:
            payload["systemInstruction"] = {
                "parts": [{"text": system_instruction}]
            }

        headers = {"Content-Type": "application/json"}
        response = requests.post(self.endpoint, json=payload, headers=headers, timeout=20)
        
        if response.status_code != 200:
            raise RuntimeError(f"Gemini API returned status {response.status_code}: {response.text}")

        data = response.json()
        candidates = data.get("candidates", [])
        if candidates and "content" in candidates[0]:
            parts = candidates[0]["content"].get("parts", [])
            if parts and "text" in parts[0]:
                return parts[0]["text"]

        raise ValueError("Invalid response structure from Gemini API")

    def parse_resume(self, raw_text: str) -> Dict[str, Any]:
        system_instruction = (
            "You are an expert technical recruiter and resume ATS parser. "
            "Analyze the resume text and return pure JSON with keys: "
            "full_name (str), email (str), phone (str), detected_skills (list of str), "
            "has_sections (dict of bools: education, projects, experience, certifications), "
            "score_breakdown (dict of int 0-100: skills, projects, keywords, education, experience), "
            "match_score (float 0-100), improvement_suggestions (list of str)."
        )
        prompt = f"Parse and analyze this candidate resume:\n\n{raw_text[:8000]}"
        try:
            raw_json = self._call_gemini(prompt, system_instruction)
            parsed = json.loads(raw_json)
            # Ensure mandatory fields exist
            if 'match_score' in parsed and 'score_breakdown' in parsed:
                return parsed
        except Exception as e:
            logger.warning("Gemini resume parsing failed; using fallback. Error: %s", str(e))
        return self.fallback.parse_resume(raw_text)

    def analyze_job_description(self, raw_text: str) -> Dict[str, Any]:
        system_instruction = (
            "You are a talent acquisition specialist. "
            "Extract structured data from the job description and return JSON with keys: "
            "title (str), company (str), employment_type (str: INTERNSHIP or FULL_TIME), "
            "location (str), required_skills (list of str), preferred_skills (list of str), "
            "experience_level (str), education_requirements (str), responsibilities (list of str)."
        )
        prompt = f"Analyze this job posting:\n\n{raw_text[:6000]}"
        try:
            raw_json = self._call_gemini(prompt, system_instruction)
            return json.loads(raw_json)
        except Exception as e:
            logger.warning("Gemini job analysis failed; using fallback. Error: %s", str(e))
        return self.fallback.analyze_job_description(raw_text)

    def match_profile_and_resume_to_job(
        self,
        profile_data: Dict[str, Any],
        resume_data: Dict[str, Any],
        job_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        system_instruction = (
            "You are an objective hiring analyst. Evaluate candidate fit against the job requirement. "
            "Return JSON with: job_match_score (float 0-100), breakdown (skills, experience, education, keywords), "
            "matched_skills (list of str), missing_skills (list of str), "
            "related_skills (list of objects with user_skill, job_skill, rationale), "
            "disclaimer (must state analysis identifies areas of alignment without predicting hiring), "
            "checklist (list of 4 practical preparation action items)."
        )
        prompt = (
            f"Candidate Skills: {profile_data.get('skills', [])}\n"
            f"Resume Detected Skills: {resume_data.get('detected_skills', [])}\n"
            f"Job Title: {job_data.get('title')}\n"
            f"Job Required Skills: {job_data.get('required_skills', [])}\n"
            f"Job Preferred Skills: {job_data.get('preferred_skills', [])}"
        )
        try:
            raw_json = self._call_gemini(prompt, system_instruction)
            return json.loads(raw_json)
        except Exception as e:
            logger.warning("Gemini match analysis failed; using fallback. Error: %s", str(e))
        return self.fallback.match_profile_and_resume_to_job(profile_data, resume_data, job_data)

    def generate_career_insights(
        self,
        user_data: Dict[str, Any],
        tracked_jobs: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        return self.fallback.generate_career_insights(user_data, tracked_jobs)

    def generate_interview_questions(
        self,
        job_data: Dict[str, Any],
        skills: List[str]
    ) -> List[Dict[str, Any]]:
        return self.fallback.generate_interview_questions(job_data, skills)

    def generate_cover_letter(
        self,
        user_profile: Dict[str, Any],
        job_data: Dict[str, Any]
    ) -> str:
        system_instruction = "Write a compelling, professional cover letter for an internship or junior developer role."
        prompt = (
            f"Candidate: {user_profile.get('full_name', 'Candidate')}\n"
            f"Skills: {user_profile.get('skills', [])}\n"
            f"Target Role: {job_data.get('title', 'Software Developer')}\n"
            f"Company: {job_data.get('company', 'Tech Co')}\n"
            f"Keep it within 3 concise paragraphs."
        )
        try:
            return self._call_gemini(prompt, system_instruction)
        except Exception:
            return self.fallback.generate_cover_letter(user_profile, job_data)
