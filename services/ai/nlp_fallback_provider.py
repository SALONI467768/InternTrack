import re
from typing import Dict, Any, List
from .base import BaseAIProvider

# Comprehensive skill taxonomy catalog with categories and aliases
KNOWN_SKILLS = {
    # Languages
    'python': {'name': 'Python', 'category': 'LANGUAGES', 'related': ['Django', 'FastAPI', 'Flask']},
    'javascript': {'name': 'JavaScript', 'category': 'LANGUAGES', 'related': ['TypeScript', 'React', 'Node.js']},
    'typescript': {'name': 'TypeScript', 'category': 'LANGUAGES', 'related': ['JavaScript', 'React', 'Angular']},
    'java': {'name': 'Java', 'category': 'LANGUAGES', 'related': ['Spring Boot', 'Kotlin']},
    'c++': {'name': 'C++', 'category': 'LANGUAGES', 'related': ['C', 'DSA']},
    'c#': {'name': 'C#', 'category': 'LANGUAGES', 'related': ['.NET', 'ASP.NET']},
    'go': {'name': 'Go', 'category': 'LANGUAGES', 'related': ['Docker', 'Kubernetes']},
    'sql': {'name': 'SQL', 'category': 'DATABASES', 'related': ['PostgreSQL', 'MySQL']},
    'html': {'name': 'HTML', 'category': 'FRAMEWORKS', 'related': ['CSS', 'JavaScript']},
    'css': {'name': 'CSS', 'category': 'FRAMEWORKS', 'related': ['Bootstrap', 'Tailwind CSS']},

    # Frameworks
    'django': {'name': 'Django', 'category': 'FRAMEWORKS', 'related': ['Flask', 'FastAPI', 'DRF']},
    'django rest framework': {'name': 'Django REST Framework', 'category': 'FRAMEWORKS', 'related': ['Django', 'REST API']},
    'drf': {'name': 'Django REST Framework', 'category': 'FRAMEWORKS', 'related': ['Django', 'REST API']},
    'flask': {'name': 'Flask', 'category': 'FRAMEWORKS', 'related': ['Django', 'FastAPI']},
    'fastapi': {'name': 'FastAPI', 'category': 'FRAMEWORKS', 'related': ['Django', 'Flask']},
    'react': {'name': 'React', 'category': 'FRAMEWORKS', 'related': ['JavaScript', 'TypeScript', 'Next.js']},
    'node.js': {'name': 'Node.js', 'category': 'FRAMEWORKS', 'related': ['Express', 'JavaScript']},
    'express': {'name': 'Express', 'category': 'FRAMEWORKS', 'related': ['Node.js', 'REST API']},
    'tailwind': {'name': 'Tailwind CSS', 'category': 'FRAMEWORKS', 'related': ['CSS', 'Bootstrap']},
    'bootstrap': {'name': 'Bootstrap', 'category': 'FRAMEWORKS', 'related': ['CSS', 'Tailwind CSS']},

    # Databases
    'postgresql': {'name': 'PostgreSQL', 'category': 'DATABASES', 'related': ['MySQL', 'SQL']},
    'postgres': {'name': 'PostgreSQL', 'category': 'DATABASES', 'related': ['MySQL', 'SQL']},
    'mysql': {'name': 'MySQL', 'category': 'DATABASES', 'related': ['PostgreSQL', 'SQL']},
    'mongodb': {'name': 'MongoDB', 'category': 'DATABASES', 'related': ['NoSQL', 'Redis']},
    'redis': {'name': 'Redis', 'category': 'DATABASES', 'related': ['Celery', 'Caching', 'Memcached']},

    # DevOps & Tools
    'docker': {'name': 'Docker', 'category': 'DEVOPS', 'related': ['Kubernetes', 'CI/CD']},
    'kubernetes': {'name': 'Kubernetes', 'category': 'DEVOPS', 'related': ['Docker', 'AWS']},
    'git': {'name': 'Git', 'category': 'TOOLS', 'related': ['GitHub', 'GitLab']},
    'github': {'name': 'GitHub', 'category': 'TOOLS', 'related': ['Git', 'CI/CD']},
    'linux': {'name': 'Linux', 'category': 'TOOLS', 'related': ['Bash', 'DevOps']},
    'celery': {'name': 'Celery', 'category': 'DEVOPS', 'related': ['Redis', 'RabbitMQ', 'Django']},
    'aws': {'name': 'AWS', 'category': 'CLOUD', 'related': ['Cloud', 'Docker']},

    # Architecture & Fundamentals
    'rest api': {'name': 'REST API', 'category': 'FUNDAMENTALS', 'related': ['Django REST Framework', 'FastAPI']},
    'oop': {'name': 'Object-Oriented Programming (OOP)', 'category': 'FUNDAMENTALS', 'related': ['Python', 'Java']},
    'dsa': {'name': 'Data Structures & Algorithms', 'category': 'FUNDAMENTALS', 'related': ['Problem Solving', 'Python']},
    'jwt': {'name': 'JWT Authentication', 'category': 'FUNDAMENTALS', 'related': ['REST API', 'Security']},
    'microservices': {'name': 'Microservices', 'category': 'FUNDAMENTALS', 'related': ['Docker', 'REST API']},
}

RELATED_SKILL_PAIRS = {
    'flask': {'target': 'Django', 'rationale': 'Flask provides foundational Python web routing and WSGI knowledge transferable to Django.'},
    'mysql': {'target': 'PostgreSQL', 'rationale': 'Relational DB concepts, ACID transactions, and SQL syntax directly transfer to PostgreSQL.'},
    'express': {'target': 'Django REST Framework', 'rationale': 'REST API design patterns and middleware concepts carry over smoothly.'},
    'docker': {'target': 'Kubernetes', 'rationale': 'Containerization experience is the prerequisite foundation for container orchestration.'},
    'javascript': {'target': 'TypeScript', 'rationale': 'TypeScript is a typed superset of JavaScript, making syntax familiar.'},
}

class LocalNLPFallbackProvider(BaseAIProvider):
    """
    Deterministic rule-based and NLP keyword extraction engine.
    Ensures zero external dependency downtime and works 100% offline.
    """

    def parse_resume(self, raw_text: str) -> Dict[str, Any]:
        text_lower = raw_text.lower()

        # 1. Contact Info Extraction
        email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', raw_text)
        email = email_match.group(0) if email_match else ''

        phone_match = re.search(r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', raw_text)
        phone = phone_match.group(0) if phone_match else ''

        # Name extraction heuristic (first non-empty line or header)
        lines = [line.strip() for line in raw_text.split('\n') if line.strip()]
        full_name = lines[0] if lines and len(lines[0]) < 50 and not any(c in lines[0] for c in ['@', 'http', 'github']) else 'Candidate'

        # 2. Section Detection
        has_education = any(k in text_lower for k in ['education', 'degree', 'university', 'b.tech', 'bachelor', 'master'])
        has_projects = any(k in text_lower for k in ['projects', 'personal projects', 'academic projects'])
        has_experience = any(k in text_lower for k in ['experience', 'work experience', 'internship', 'employment'])
        has_certifications = any(k in text_lower for k in ['certifications', 'certificates', 'licenses'])

        # 3. Skills Detection
        detected_skills = []
        for key, meta in KNOWN_SKILLS.items():
            pattern = r'\b' + re.escape(key) + r'\b'
            if re.search(pattern, text_lower):
                if meta['name'] not in detected_skills:
                    detected_skills.append(meta['name'])

        # 4. Score Calculation (InternTrack Resume Match Score 0-100)
        skills_score = min(100, int((len(detected_skills) / 8) * 100)) if detected_skills else 20
        projects_score = 85 if has_projects and len(detected_skills) >= 4 else (65 if has_projects else 30)
        keywords_score = min(100, int((len(detected_skills) / 10) * 100))
        education_score = 90 if has_education else 40
        experience_score = 80 if has_experience else 50

        # Weighted calculation
        total_score = round(
            (skills_score * 0.35) +
            (projects_score * 0.25) +
            (keywords_score * 0.15) +
            (education_score * 0.15) +
            (experience_score * 0.10),
            1
        )

        suggestions = []
        if len(detected_skills) < 6:
            suggestions.append("Enrich your technical skills section with specific frameworks, databases, and version control tools.")
        if not has_projects:
            suggestions.append("Add 2-3 substantial projects detailing the technologies used, architecture, and live demo links.")
        if not has_experience:
            suggestions.append("Include internship, open-source contributions, or freelance project experience with quantifiable outcomes.")
        if 'docker' not in text_lower and 'git' not in text_lower:
            suggestions.append("Add foundational developer tools like Git and Docker to boost industry relevance.")

        if not suggestions:
            suggestions.append("Strong resume structure! Tailor bullet points with measurable impact metrics (e.g., 'improved query speed by 30%').")

        return {
            'full_name': full_name,
            'email': email,
            'phone': phone,
            'detected_skills': detected_skills,
            'has_sections': {
                'education': has_education,
                'projects': has_projects,
                'experience': has_experience,
                'certifications': has_certifications,
            },
            'score_breakdown': {
                'skills': skills_score,
                'projects': projects_score,
                'keywords': keywords_score,
                'education': education_score,
                'experience': experience_score,
            },
            'match_score': total_score,
            'improvement_suggestions': suggestions
        }

    def analyze_job_description(self, raw_text: str) -> Dict[str, Any]:
        text_lower = raw_text.lower()

        # Title heuristic
        title = "Software Engineer"
        for candidate_title in [
            "Full Stack Developer", "Python Developer", "Backend Developer", "Frontend Developer",
            "Software Development Engineer Intern", "Software Engineering Intern", "DevOps Engineer",
            "Data Analyst", "Machine Learning Intern"
        ]:
            if candidate_title.lower() in text_lower:
                title = candidate_title
                break

        # Company heuristic
        company_match = re.search(r'(?:at|company:?|about)\s+([A-Z][A-Za-z0-9\s&]{2,30})', raw_text)
        company = company_match.group(1).strip() if company_match else "Target Company"

        # Employment type
        emp_type = "INTERNSHIP" if any(k in text_lower for k in ['intern', 'internship', 'trainee', 'stipend']) else "FULL_TIME"

        # Required skills extraction
        extracted_skills = []
        for key, meta in KNOWN_SKILLS.items():
            pattern = r'\b' + re.escape(key) + r'\b'
            if re.search(pattern, text_lower):
                if meta['name'] not in extracted_skills:
                    extracted_skills.append(meta['name'])

        required_skills = extracted_skills[:6] if len(extracted_skills) >= 6 else extracted_skills
        preferred_skills = extracted_skills[6:] if len(extracted_skills) > 6 else []

        # Responsibilities extraction (lines with bullet points or dashes)
        responsibilities = []
        for line in raw_text.split('\n'):
            line_str = line.strip()
            if line_str.startswith(('-', '*', '•')) and len(line_str) > 15:
                responsibilities.append(line_str.lstrip('-*• ').strip())
            if len(responsibilities) >= 5:
                break

        return {
            'title': title,
            'company': company,
            'employment_type': emp_type,
            'location': "Remote / Flexible",
            'required_skills': required_skills,
            'preferred_skills': preferred_skills,
            'experience_level': "Fresher / 0-2 Years",
            'education_requirements': "B.Tech/B.E./BCA/MCA/B.S. in Computer Science or related field",
            'responsibilities': responsibilities
        }

    def match_profile_and_resume_to_job(
        self,
        profile_data: Dict[str, Any],
        resume_data: Dict[str, Any],
        job_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        user_skills = set(s.lower() for s in profile_data.get('skills', []))
        resume_skills = set(s.lower() for s in resume_data.get('detected_skills', []))
        all_user_skills = user_skills.union(resume_skills)

        job_required = [s.lower() for s in job_data.get('required_skills', [])]
        job_preferred = [s.lower() for s in job_data.get('preferred_skills', [])]
        all_job_skills = list(dict.fromkeys(job_required + job_preferred))

        matched = []
        missing = []
        related = []

        for req in all_job_skills:
            if req in all_user_skills:
                matched.append(req.title())
            else:
                # Check for related skills
                found_related = False
                for u_skill in all_user_skills:
                    if u_skill in RELATED_SKILL_PAIRS and RELATED_SKILL_PAIRS[u_skill]['target'].lower() == req:
                        related.append({
                            'user_skill': u_skill.title(),
                            'job_skill': req.title(),
                            'rationale': RELATED_SKILL_PAIRS[u_skill]['rationale']
                        })
                        found_related = True
                        break
                if not found_related:
                    missing.append(req.title())

        total_req = len(all_job_skills)
        if total_req > 0:
            skills_score = round(((len(matched) + (len(related) * 0.5)) / total_req) * 100, 1)
        else:
            skills_score = 75.0

        skills_score = min(100.0, max(15.0, skills_score))
        exp_score = 70.0
        edu_score = 90.0
        kw_score = min(100.0, skills_score + 5.0)

        job_match_score = round(
            (skills_score * 0.50) +
            (exp_score * 0.20) +
            (edu_score * 0.15) +
            (kw_score * 0.15),
            1
        )

        return {
            'job_match_score': job_match_score,
            'breakdown': {
                'skills': skills_score,
                'experience': exp_score,
                'education': edu_score,
                'keywords': kw_score,
            },
            'matched_skills': matched,
            'missing_skills': missing,
            'related_skills': related,
            'disclaimer': 'This analysis identifies areas of alignment and potential gaps. It does not predict hiring decisions.',
            'checklist': [
                f"Review fundamental syntax and typical design patterns for {', '.join(missing[:3]) if missing else 'core languages'}.",
                "Prepare concise STAR-format walkthroughs for your primary portfolio projects.",
                "Review SQL query optimization and indexing questions.",
                "Verify that your resume emphasizes the matched skills prominently."
            ]
        }

    def generate_career_insights(
        self,
        user_data: Dict[str, Any],
        tracked_jobs: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        insights = []
        user_skills = set(s.lower() for s in user_data.get('skills', []))
        total_tracked = len(tracked_jobs)

        if total_tracked > 0:
            insights.append({
                'category': 'VOLUME',
                'title': f"Active Pipeline Volume: {total_tracked} Positions",
                'body': f"You have tracked {total_tracked} roles in your pipeline. Maintaining a steady pace of 5-8 tailored applications weekly maximizes response rates.",
                'type': 'INFO'
            })

            # Skill frequency in tracked jobs
            freq = {}
            for j in tracked_jobs:
                for req in j.get('required_skills', []):
                    req_lower = req.lower()
                    freq[req_lower] = freq.get(req_lower, 0) + 1

            sorted_freq = sorted(freq.items(), key=lambda x: x[1], reverse=True)
            top_skills = [s[0].title() for s in sorted_freq[:4]]

            if top_skills:
                insights.append({
                    'category': 'MARKET_DEMAND',
                    'title': 'High-Frequency Skills Detected',
                    'body': f"{', '.join(top_skills)} appear most frequently in your saved job descriptions.",
                    'type': 'SUCCESS'
                })

            # Missing high-frequency skills
            high_freq_missing = [s[0].title() for s in sorted_freq if s[0] not in user_skills and s[1] >= 2]
            if high_freq_missing:
                insights.append({
                    'category': 'OPPORTUNITY_GAP',
                    'title': f"High-ROI Learning Focus: {', '.join(high_freq_missing[:3])}",
                    'body': f"Several saved roles mention {', '.join(high_freq_missing[:3])}, but they are not currently listed in your profile. Adding projects with these will significantly raise your match rate.",
                    'type': 'WARNING'
                })
        else:
            insights.append({
                'category': 'GETTING_STARTED',
                'title': 'Start Tracking Target Roles',
                'body': 'Paste or add 3-5 target job descriptions to unlock personalized skill gap intelligence and company insights.',
                'type': 'INFO'
            })

        return insights

    def generate_interview_questions(
        self,
        job_data: Dict[str, Any],
        skills: List[str]
    ) -> List[Dict[str, Any]]:
        questions = [
            {
                'category': 'Python',
                'question_type': 'TECHNICAL',
                'difficulty': 'MEDIUM',
                'question': 'How does Python handle memory management and garbage collection?',
                'model_answer': 'Python uses reference counting as its primary memory management mechanism, complemented by a generational cyclic garbage collector to detect and collect reference cycles.',
                'explanation': 'Explain reference counting (PyObject ob_refcnt) and how gc module handles unreachable cyclic references in three generations (Gen 0, 1, 2).'
            },
            {
                'category': 'Django',
                'question_type': 'TECHNICAL',
                'difficulty': 'MEDIUM',
                'question': 'What is the N+1 queries problem in Django ORM and how do you resolve it?',
                'model_answer': 'The N+1 problem occurs when querying parent records executes 1 query, and accessing a related field executes an additional query for each of the N child records. It is resolved using select_related() for single-valued relationships (ForeignKey, OneToOne) and prefetch_related() for multi-valued relationships (ManyToMany, reverse FK).',
                'explanation': 'select_related does an SQL JOIN, while prefetch_related does a second query with IN clause and matches in Python.'
            },
            {
                'category': 'REST API',
                'question_type': 'TECHNICAL',
                'difficulty': 'EASY',
                'question': 'What is idempotency in REST APIs, and which HTTP methods are idempotent?',
                'model_answer': 'An HTTP method is idempotent if executing the exact same request multiple times produces the identical side-effect on the server as executing it once. GET, PUT, DELETE, HEAD, and OPTIONS are idempotent. POST is NOT idempotent.',
                'explanation': 'Making 5 PUT requests to update a resource yields the same state. Making 5 POST requests creates 5 distinct resources.'
            },
            {
                'category': 'SQL',
                'question_type': 'SQL',
                'difficulty': 'MEDIUM',
                'question': 'Explain the difference between WHERE and HAVING clauses.',
                'model_answer': 'WHERE filters individual rows before any grouping or aggregation takes place. HAVING filters grouped rows after aggregate functions (such as COUNT, SUM, AVG) have been evaluated.',
                'explanation': 'WHERE cannot refer to aggregate expressions unless nested in a subquery; HAVING operates directly on aggregated buckets.'
            },
            {
                'category': 'HR',
                'question_type': 'HR',
                'difficulty': 'EASY',
                'question': 'Tell me about a challenging technical bug you encountered in a project and how you solved it.',
                'model_answer': 'Structure using the STAR method: Situation, Task, Action, and Result. Highlight systematic debugging (logs, breakpoints, unit test recreation) rather than random trial-and-error.',
                'explanation': 'Interviewers evaluate your diagnostic methodology, persistence, and ability to communicate complex issues cleanly.'
            }
        ]
        return questions

    def generate_cover_letter(
        self,
        user_profile: Dict[str, Any],
        job_data: Dict[str, Any]
    ) -> str:
        name = user_profile.get('full_name') or 'Candidate'
        title = job_data.get('title') or 'Software Engineer'
        company = job_data.get('company') or 'the Team'
        skills = ', '.join(user_profile.get('skills', ['Python', 'Django', 'SQL'])[:4])

        return (
            f"Dear Hiring Team at {company},\n\n"
            f"I am writing to express my strong enthusiasm for the {title} position. "
            f"With a solid foundation in {skills} and practical experience architecting scalable full-stack applications, "
            f"I am eager to contribute effectively to your team's engineering goals.\n\n"
            f"Throughout my projects, I have focused on clean code, RESTful API design, database optimization, "
            f"and automated testing. The mission and engineering challenges at {company} align closely with my technical passion.\n\n"
            f"Thank you for your time and consideration. I welcome the opportunity to discuss how my skill set can benefit {company}.\n\n"
            f"Sincerely,\n{name}"
        )
