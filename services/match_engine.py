from typing import Dict, Any
from apps.resumes.models import Resume
from apps.skills.models import UserSkill
from services.ai import get_ai_provider

def compute_job_match(user, job) -> Dict[str, Any]:
    """
    Computes explainable Job Match Score and gap analysis between a user's
    profile/resume and a specific job posting.
    """
    # 1. Fetch user skills
    user_skills_qs = UserSkill.objects.filter(user=user).select_related('skill')
    user_skill_names = [us.skill.name for us in user_skills_qs]

    profile_data = {
        'full_name': getattr(user.profile, 'full_name', ''),
        'target_role': getattr(user.profile, 'target_role', ''),
        'college': getattr(user.profile, 'college', ''),
        'degree': getattr(user.profile, 'degree', ''),
        'skills': user_skill_names,
    }

    # 2. Fetch primary resume
    primary_resume = Resume.objects.filter(user=user, is_primary=True).first()
    if not primary_resume:
        primary_resume = Resume.objects.filter(user=user).order_by('-created_at').first()

    resume_data = {
        'detected_skills': [rs.skill.name for rs in primary_resume.resume_skills.select_related('skill')] if primary_resume else [],
        'has_resume': primary_resume is not None,
    }

    # 3. Job skills
    job_skills_qs = job.job_skills.select_related('skill')
    required_skills = [js.skill.name for js in job_skills_qs if js.is_critical]
    preferred_skills = [js.skill.name for js in job_skills_qs if not js.is_critical]

    job_data = {
        'title': job.title,
        'company': job.company,
        'location': job.location,
        'employment_type': job.employment_type,
        'required_skills': required_skills,
        'preferred_skills': preferred_skills,
    }

    ai_provider = get_ai_provider()
    match_result = ai_provider.match_profile_and_resume_to_job(profile_data, resume_data, job_data)
    match_result['has_primary_resume'] = primary_resume is not None
    match_result['primary_resume_name'] = primary_resume.file_name if primary_resume else None

    return match_result
