from .models import LearningRoadmap, LearningTask
from apps.skills.models import Skill, UserSkill


DEFAULT_ROADMAP_CURRICULUM = [
    {
        'week': 1,
        'topic': 'Django Basics & MTV Architecture',
        'skill': 'Django',
        'priority': 'CRITICAL',
        'hours': 8.0,
        'description': 'Master models, migrations, views, templates, and URL routing in Django.',
        'practice': 'Build a CRUD blog application with custom models and slug-based URLs.'
    },
    {
        'week': 2,
        'topic': 'Django REST Framework & Serializers',
        'skill': 'Django REST Framework',
        'priority': 'CRITICAL',
        'hours': 10.0,
        'description': 'Understand ModelSerializers, ViewSets, Routers, and pagination.',
        'practice': 'Create a RESTful API with ModelViewSet, custom validation, and token authentication.'
    },
    {
        'week': 3,
        'topic': 'PostgreSQL & Database Optimization',
        'skill': 'PostgreSQL',
        'priority': 'IMPORTANT',
        'hours': 6.0,
        'description': 'Learn indexing strategies, query profiling with EXPLAIN ANALYZE, and ACID guarantees.',
        'practice': 'Optimize 3 slow N+1 query patterns using select_related() and prefetch_related().'
    },
    {
        'week': 4,
        'topic': 'JWT Authentication & Security Best Practices',
        'skill': 'JWT Authentication',
        'priority': 'CRITICAL',
        'hours': 6.0,
        'description': 'Implement access and refresh token lifecycle, token blacklisting, and CORS policies.',
        'practice': 'Secure all private API endpoints with SimpleJWT and custom permission classes.'
    },
    {
        'week': 5,
        'topic': 'Docker Containerization & Deployment',
        'skill': 'Docker',
        'priority': 'IMPORTANT',
        'hours': 7.0,
        'description': 'Write multi-stage Dockerfiles and orchestrate web, database, and Redis with docker-compose.',
        'practice': 'Containerize this full-stack application and run with docker-compose up --build.'
    },
]


def generate_roadmap_for_user(user, target_role="Full Stack Developer"):
    """Creates a structured roadmap tailored to the user's role and skill gaps."""
    roadmap, _ = LearningRoadmap.objects.get_or_create(
        user=user,
        defaults={'target_role': target_role}
    )

    # If tasks already exist, return roadmap
    if roadmap.tasks.exists():
        return roadmap

    # Identify user's existing skills
    user_skills = set(us.skill.name.lower() for us in user.user_skills.select_related('skill'))

    for item in DEFAULT_ROADMAP_CURRICULUM:
        skill_obj, _ = Skill.objects.get_or_create(
            name=item['skill'],
            defaults={'category': 'FRAMEWORKS'}
        )
        LearningTask.objects.create(
            roadmap=roadmap,
            skill=skill_obj,
            week_number=item['week'],
            topic=item['topic'],
            description=item['description'],
            priority=item['priority'],
            status='COMPLETED' if skill_obj.name.lower() in user_skills else 'NOT_STARTED',
            estimated_hours=item['hours'],
            practice_task=item['practice']
        )

    roadmap.recalculate_progress()
    return roadmap
