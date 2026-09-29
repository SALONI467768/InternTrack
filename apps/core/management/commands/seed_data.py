from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from apps.skills.models import Skill, UserSkill
from apps.jobs.models import Job, JobSkill
from apps.applications.models import Application, ApplicationStatusHistory, FollowUp
from apps.interviews.models import Interview, InterviewQuestion, InterviewAttempt
from apps.learning.models import LearningRoadmap, LearningTask
from apps.notifications.models import Notification
from apps.core.models import ActivityLog

User = get_user_model()

SKILLS_SEED = [
    # Languages
    ('Python', 'LANGUAGES', ['py', 'python3']),
    ('JavaScript', 'LANGUAGES', ['js', 'es6']),
    ('TypeScript', 'LANGUAGES', ['ts']),
    ('Java', 'LANGUAGES', ['java8', 'java17']),
    ('C++', 'LANGUAGES', ['cpp']),
    ('SQL', 'DATABASES', ['structured query language']),
    ('HTML', 'FRAMEWORKS', ['html5']),
    ('CSS', 'FRAMEWORKS', ['css3']),

    # Frameworks
    ('Django', 'FRAMEWORKS', ['django-framework']),
    ('Django REST Framework', 'FRAMEWORKS', ['drf', 'django rest']),
    ('FastAPI', 'FRAMEWORKS', ['fast-api']),
    ('Flask', 'FRAMEWORKS', ['flask-python']),
    ('React', 'FRAMEWORKS', ['reactjs', 'react.js']),
    ('Node.js', 'FRAMEWORKS', ['nodejs']),
    ('Tailwind CSS', 'FRAMEWORKS', ['tailwind']),
    ('Bootstrap', 'FRAMEWORKS', ['bootstrap5']),

    # Databases
    ('PostgreSQL', 'DATABASES', ['postgres', 'psql']),
    ('MySQL', 'DATABASES', ['mysql-db']),
    ('Redis', 'DATABASES', ['redis-cache']),
    ('MongoDB', 'DATABASES', ['mongo']),

    # DevOps & Cloud
    ('Docker', 'DEVOPS', ['containerization']),
    ('Kubernetes', 'DEVOPS', ['k8s']),
    ('AWS', 'CLOUD', ['amazon web services', 'ec2', 's3']),
    ('Git', 'TOOLS', ['git-vcs']),
    ('GitHub', 'TOOLS', ['github-actions']),
    ('Linux', 'TOOLS', ['bash', 'unix']),
    ('Celery', 'DEVOPS', ['celery-task']),

    # Fundamentals
    ('REST API', 'FUNDAMENTALS', ['restful apis', 'api design']),
    ('OOP', 'FUNDAMENTALS', ['object oriented programming']),
    ('Data Structures & Algorithms', 'FUNDAMENTALS', ['dsa', 'algorithms']),
    ('JWT Authentication', 'FUNDAMENTALS', ['jwt', 'json web tokens']),
]

QUESTIONS_SEED = [
    {
        'category': 'Python',
        'question_type': 'TECHNICAL',
        'difficulty': 'MEDIUM',
        'question_text': 'Explain the difference between deepcopy and shallow copy in Python.',
        'model_answer': 'A shallow copy constructs a new compound object and inserts references into it to the objects found in the original. A deepcopy constructs a new compound object and recursively copies all objects found in the original, ensuring complete independence.',
        'explanation': 'Use copy.copy() for shallow copies and copy.deepcopy() for nested mutable structures like dicts of lists.'
    },
    {
        'category': 'Django',
        'question_type': 'TECHNICAL',
        'difficulty': 'MEDIUM',
        'question_text': 'How does Django ORM handle migrations and schema evolution safely?',
        'model_answer': 'Django creates migration files reflecting changes to Python models using makemigrations. Running migrate applies these changes in dependency order, tracking executed migrations in the django_migrations database table wrapped inside atomic transactions.',
        'explanation': 'Always review generated SQL with python manage.py sqlmigrate before applying migrations in production.'
    },
    {
        'category': 'REST API',
        'question_type': 'TECHNICAL',
        'difficulty': 'EASY',
        'question_text': 'What HTTP status codes should be returned for successful creation, validation error, and unauthorized access?',
        'model_answer': '201 Created for resource creation, 400 Bad Request (or 422 Unprocessable Entity) for client validation errors, and 401 Unauthorized when authentication credentials are missing or invalid.',
        'explanation': 'Distinguish 401 Unauthorized (unauthenticated) from 403 Forbidden (authenticated but lacking permissions).'
    },
    {
        'category': 'SQL',
        'question_type': 'SQL',
        'difficulty': 'MEDIUM',
        'question_text': 'What is database indexing and what are the trade-offs of having too many indexes?',
        'model_answer': 'An index (typically B-Tree) speeds up data retrieval queries (SELECT with WHERE, JOIN, ORDER BY) by avoiding full table scans. The trade-offs are increased storage overhead and slower write performance (INSERT, UPDATE, DELETE) since each index must be updated on modification.',
        'explanation': 'Index high-cardinality foreign keys and frequently filtered columns, but avoid indexing low-cardinality columns like boolean flags.'
    },
    {
        'category': 'HR',
        'question_type': 'HR',
        'difficulty': 'EASY',
        'question_text': 'Why are you interested in a Backend/Full-Stack Software Engineering role?',
        'model_answer': 'I enjoy turning complex business requirements into robust, high-performance web APIs and reliable systems. I take pride in designing clean relational schemas, ensuring fast query responses, and building user-centric interfaces that solve real-world problems.',
        'explanation': 'Highlight passion for problem-solving, code maintainability, and measurable impact.'
    },
]

class Command(BaseCommand):
    help = 'Seeds database with skills taxonomy, interview questions, and a demo candidate dataset'

    def handle(self, *args, **kwargs):
        self.stdout.write("Seeding Skills Taxonomy...")
        skill_objs = {}
        for name, category, aliases in SKILLS_SEED:
            skill, _ = Skill.objects.get_or_create(
                name=name,
                defaults={'category': category, 'aliases': aliases}
            )
            skill_objs[name] = skill

        self.stdout.write("Seeding Interview Questions...")
        for q in QUESTIONS_SEED:
            InterviewQuestion.objects.get_or_create(
                category=q['category'],
                question_text=q['question_text'],
                defaults=q
            )

        self.stdout.write("Creating Administrator and Demo Student Accounts...")
        admin_user, _ = User.objects.get_or_create(
            email='admin@interntrack.ai',
            defaults={
                'username': 'admin',
                'role': 'ADMIN',
                'is_staff': True,
                'is_superuser': True,
                'is_verified': True
            }
        )
        admin_user.set_password('Admin@123456')
        admin_user.save()

        demo_user, _ = User.objects.get_or_create(
            email='student@interntrack.ai',
            defaults={
                'username': 'alex_student',
                'role': 'STUDENT',
                'is_verified': True
            }
        )
        demo_user.set_password('Student@123456')
        demo_user.save()

        # Setup student profile
        profile = demo_user.profile
        profile.full_name = "Alex Morgan"
        profile.phone = "+1 (555) 382-9102"
        profile.location = "San Francisco, CA"
        profile.bio = "Passionate full-stack Python & Django developer eager to build scalable web platforms and data pipelines."
        profile.target_role = "Python Backend Developer"
        profile.college = "California State University"
        profile.degree = "B.S. in Computer Science"
        profile.graduation_year = 2026
        profile.github_url = "https://github.com/example-alex"
        profile.linkedin_url = "https://linkedin.com/in/example-alex"
        profile.portfolio_url = "https://alex-dev-portfolio.com"
        profile.work_mode_preference = "HYBRID"
        profile.expected_salary = "$8,000 / month (or $45/hr)"
        profile.projects = [
            {
                "title": "Distributed Task Queue Visualizer",
                "description": "Real-time Celery worker monitoring dashboard using Redis and WebSockets.",
                "tech_stack": "Python, Django, Celery, Redis"
            },
            {
                "title": "E-Commerce REST Microservice",
                "description": "High-throughput catalog service with PostgreSQL indexing and JWT auth.",
                "tech_stack": "Django REST Framework, PostgreSQL, Docker"
            }
        ]
        profile.save()

        # Attach student skills
        self.stdout.write("Attaching Student Skills...")
        student_skills = [
            ('Python', 'ADVANCED', 2.5),
            ('Django', 'ADVANCED', 2.0),
            ('Django REST Framework', 'INTERMEDIATE', 1.5),
            ('SQL', 'INTERMEDIATE', 2.0),
            ('PostgreSQL', 'INTERMEDIATE', 1.5),
            ('Git', 'ADVANCED', 3.0),
            ('JavaScript', 'INTERMEDIATE', 1.5),
            ('HTML', 'ADVANCED', 3.0),
            ('CSS', 'INTERMEDIATE', 2.0),
            ('REST API', 'ADVANCED', 2.0),
        ]
        for s_name, prof_level, yrs in student_skills:
            if s_name in skill_objs:
                UserSkill.objects.get_or_create(
                    user=demo_user,
                    skill=skill_objs[s_name],
                    defaults={'proficiency': prof_level, 'years_of_experience': yrs}
                )

        profile.calculate_completion()
        profile.save()

        # Seed tracked jobs and applications
        self.stdout.write("Seeding Tracked Jobs & Applications...")
        jobs_data = [
            {
                'company': 'CloudScale Dynamics',
                'title': 'Python Backend Engineering Intern',
                'location': 'San Francisco, CA (Hybrid)',
                'employment_type': 'INTERNSHIP',
                'salary_range': '$45 - $55 / hour',
                'status': 'INTERVIEW',
                'applied_days_ago': 14,
                'req_skills': ['Python', 'Django', 'PostgreSQL', 'REST API'],
                'pref_skills': ['Docker', 'Redis', 'AWS']
            },
            {
                'company': 'FinVanguard Technologies',
                'title': 'Junior Full Stack Developer',
                'location': 'New York, NY (Remote)',
                'employment_type': 'FULL_TIME',
                'salary_range': '$90,000 - $105,000',
                'status': 'OFFER',
                'applied_days_ago': 28,
                'req_skills': ['Python', 'Django REST Framework', 'SQL', 'JavaScript'],
                'pref_skills': ['React', 'Celery', 'Docker']
            },
            {
                'company': 'Nexus Data Systems',
                'title': 'Software Engineering Intern - Platform',
                'location': 'Austin, TX (Remote)',
                'employment_type': 'INTERNSHIP',
                'salary_range': '$40 / hour',
                'status': 'ASSESSMENT',
                'applied_days_ago': 7,
                'req_skills': ['Python', 'SQL', 'Git', 'Data Structures & Algorithms'],
                'pref_skills': ['Docker', 'Linux']
            },
            {
                'company': 'Starlight AI Labs',
                'title': 'AI Software Intern',
                'location': 'Seattle, WA',
                'employment_type': 'INTERNSHIP',
                'salary_range': '$50 / hour',
                'status': 'APPLIED',
                'applied_days_ago': 3,
                'req_skills': ['Python', 'FastAPI', 'Docker', 'REST API'],
                'pref_skills': ['Kubernetes', 'PostgreSQL']
            },
            {
                'company': 'Apex Mobility Inc',
                'title': 'Backend Systems Intern',
                'location': 'San Jose, CA',
                'employment_type': 'INTERNSHIP',
                'salary_range': '$42 / hour',
                'status': 'REJECTED',
                'applied_days_ago': 21,
                'req_skills': ['C++', 'Linux', 'Python'],
                'pref_skills': ['Docker', 'Git']
            },
            {
                'company': 'HyperLoop Analytics',
                'title': 'Data Engineering Intern',
                'location': 'Remote',
                'employment_type': 'INTERNSHIP',
                'salary_range': '$38 / hour',
                'status': 'SAVED',
                'applied_days_ago': 0,
                'req_skills': ['Python', 'SQL', 'PostgreSQL'],
                'pref_skills': ['AWS', 'Docker']
            }
        ]

        now = timezone.now()
        for jd in jobs_data:
            job, _ = Job.objects.get_or_create(
                user=demo_user,
                company=jd['company'],
                title=jd['title'],
                defaults={
                    'location': jd['location'],
                    'employment_type': jd['employment_type'],
                    'salary_range': jd['salary_range'],
                    'raw_description': f"Looking for a motivated {jd['title']} with strong fundamentals in Python, databases, and API development.",
                    'parsed_requirements': {'responsibilities': ['Build clean APIs', 'Optimize queries', 'Collaborate on features']}
                }
            )

            # Link job skills
            for req in jd['req_skills']:
                if req in skill_objs:
                    JobSkill.objects.get_or_create(job=job, skill=skill_objs[req], defaults={'is_critical': True})
            for pref in jd['pref_skills']:
                if pref in skill_objs:
                    JobSkill.objects.get_or_create(job=job, skill=skill_objs[pref], defaults={'is_critical': False})

            # Create Application
            applied_date = (now - timedelta(days=jd['applied_days_ago'])).date() if jd['applied_days_ago'] > 0 else None
            app, _ = Application.objects.get_or_create(
                user=demo_user,
                job=job,
                defaults={
                    'status': jd['status'],
                    'applied_date': applied_date,
                    'salary_stipend': jd['salary_range'],
                    'source': 'LinkedIn',
                    'match_score_at_application': 82.5
                }
            )

            # History
            if jd['status'] != 'SAVED':
                ApplicationStatusHistory.objects.get_or_create(
                    application=app,
                    from_status='SAVED',
                    to_status='APPLIED',
                    defaults={'changed_at': now - timedelta(days=jd['applied_days_ago'])}
                )
                if jd['status'] in ['ASSESSMENT', 'INTERVIEW', 'OFFER', 'REJECTED']:
                    ApplicationStatusHistory.objects.get_or_create(
                        application=app,
                        from_status='APPLIED',
                        to_status=jd['status'],
                        defaults={'changed_at': now - timedelta(days=max(1, jd['applied_days_ago'] - 4))}
                    )

            # Follow-up for applied role
            if jd['status'] == 'APPLIED':
                FollowUp.objects.get_or_create(
                    user=demo_user,
                    application=app,
                    defaults={
                        'follow_up_date': (now + timedelta(days=4)).date(),
                        'notes': 'Check status with recruiter via LinkedIn InMail'
                    }
                )

            # Schedule real interview for INTERVIEW position
            if jd['status'] == 'INTERVIEW':
                Interview.objects.get_or_create(
                    user=demo_user,
                    application=app,
                    defaults={
                        'round_type': 'TECHNICAL',
                        'interview_type': 'VIDEO',
                        'scheduled_at': now + timedelta(days=2, hours=3),
                        'meeting_link': 'https://meet.google.com/abc-xyz-123',
                        'result': 'SCHEDULED'
                    }
                )

        self.stdout.write("Generating Roadmap & Smart Actions...")
        from apps.learning.utils import generate_roadmap_for_user
        roadmap = generate_roadmap_for_user(demo_user, "Python Backend Developer")

        # Seed Notifications
        Notification.objects.get_or_create(
            user=demo_user,
            title='Upcoming Technical Interview',
            defaults={
                'message': 'Your Technical Round with CloudScale Dynamics is scheduled in 2 days.',
                'notification_type': 'INTERVIEW_REMINDER',
                'link': '/interviews/'
            }
        )
        Notification.objects.get_or_create(
            user=demo_user,
            title='Follow-up Alert: Starlight AI Labs',
            defaults={
                'message': 'Application submitted 3 days ago. Scheduled follow-up in 4 days.',
                'notification_type': 'FOLLOW_UP_DUE',
                'link': '/applications/'
            }
        )

        # Seed Activity Logs
        ActivityLog.log_activity(demo_user, 'USER_LOGIN', 'User logged in successfully')
        ActivityLog.log_activity(demo_user, 'JOB_PARSED', 'Parsed job requirement for CloudScale Dynamics')
        ActivityLog.log_activity(demo_user, 'APPLICATION_CREATED', 'Applied to Python Backend Engineering Intern')
        ActivityLog.log_activity(demo_user, 'INTERVIEW_SCHEDULED', 'Scheduled Technical Round with CloudScale Dynamics')

        self.stdout.write(self.style.SUCCESS("Database seeding completed successfully!"))
        self.stdout.write(self.style.SUCCESS("Demo Student: student@interntrack.ai / Student@123456"))
        self.stdout.write(self.style.SUCCESS("Admin User: admin@interntrack.ai / Admin@123456"))
