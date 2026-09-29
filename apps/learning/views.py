from rest_framework import generics, permissions, status, views
from rest_framework.response import Response
from django.utils import timezone
from datetime import timedelta
from .models import LearningRoadmap, LearningTask
from .serializers import LearningRoadmapSerializer, LearningTaskSerializer
from .utils import generate_roadmap_for_user
from apps.skills.models import Skill, UserSkill
from apps.jobs.models import Job, JobSkill
from apps.applications.models import Application, FollowUp
from apps.interviews.models import Interview
from apps.core.models import ActivityLog

class LearningRoadmapView(views.APIView):
    """
    GET /api/learning/roadmap/
    Retrieves or dynamically synthesizes the personalized learning roadmap.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        target_role = getattr(request.user.profile, 'target_role', 'Full Stack Developer') if hasattr(request.user, 'profile') else 'Full Stack Developer'
        roadmap = LearningRoadmap.objects.filter(user=request.user).first()
        if not roadmap or not roadmap.tasks.exists():
            roadmap = generate_roadmap_for_user(request.user, target_role)

        serializer = LearningRoadmapSerializer(roadmap)
        return Response(serializer.data, status=status.HTTP_200_OK)

class LearningRoadmapRegenerateView(views.APIView):
    """
    POST /api/learning/roadmap/regenerate/
    Clears existing roadmap and regenerates fresh tasks based on updated skill gaps.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        LearningRoadmap.objects.filter(user=request.user).delete()
        target_role = getattr(request.user.profile, 'target_role', 'Full Stack Developer') if hasattr(request.user, 'profile') else 'Full Stack Developer'
        roadmap = generate_roadmap_for_user(request.user, target_role)
        
        ActivityLog.log_activity(request.user, 'ROADMAP_REGENERATED', f"Generated new learning roadmap for {target_role}")
        return Response(LearningRoadmapSerializer(roadmap).data, status=status.HTTP_200_OK)

class LearningTaskUpdateView(generics.UpdateAPIView):
    """
    PATCH /api/learning/tasks/<id>/
    Update task status (NOT_STARTED, IN_PROGRESS, COMPLETED).
    """
    serializer_class = LearningTaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return LearningTask.objects.filter(roadmap__user=self.request.user)

    def perform_update(self, serializer):
        task = serializer.save()
        roadmap = task.roadmap
        roadmap.recalculate_progress()
        
        if task.status == 'COMPLETED':
            # Add to user skills if attached to a skill
            if task.skill:
                UserSkill.objects.get_or_create(
                    user=self.request.user,
                    skill=task.skill,
                    defaults={'proficiency': 'INTERMEDIATE', 'years_of_experience': 1.0}
                )
            ActivityLog.log_activity(
                self.request.user,
                'LEARNING_TASK_COMPLETED',
                f"Completed learning task: {task.topic}"
            )

class SmartDailyActionsView(views.APIView):
    """
    GET /api/learning/daily-actions/
    Synthesizes concrete, high-priority actions for today based exclusively on real user data.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        today = timezone.localdate()
        actions = []

        # 1. Check pending follow-ups
        due_follow_ups = FollowUp.objects.filter(
            user=user,
            is_completed=False,
            follow_up_date__lte=today + timedelta(days=2)
        ).select_related('application__job')[:2]

        for fu in due_follow_ups:
            urgency = "Overdue" if fu.follow_up_date < today else ("Today" if fu.follow_up_date == today else "Soon")
            actions.append({
                'category': 'FOLLOW_UP',
                'title': f"Follow up with {fu.application.job.company}",
                'description': f"Application sent on {fu.application.applied_date or 'recently'}. Send a polite inquiry regarding next steps.",
                'badge': urgency,
                'action_url': f"/applications/{fu.application.id}/",
                'completed': False
            })

        # 2. Check upcoming interviews in next 5 days
        upcoming_interviews = Interview.objects.filter(
            user=user,
            result='SCHEDULED',
            scheduled_at__gte=timezone.now(),
            scheduled_at__lte=timezone.now() + timedelta(days=5)
        ).select_related('application__job')[:1]

        for interview in upcoming_interviews:
            actions.append({
                'category': 'INTERVIEW_PREP',
                'title': f"Prepare for {interview.application.job.company} ({interview.get_round_type_display()})",
                'description': f"Scheduled on {interview.scheduled_at.strftime('%A, %b %d')}. Review target job tech stack and practice 3 technical questions.",
                'badge': 'High Priority',
                'action_url': '/interviews/',
                'completed': False
            })

        # 3. Next pending learning task
        pending_task = LearningTask.objects.filter(
            roadmap__user=user,
            status__in=['NOT_STARTED', 'IN_PROGRESS']
        ).first()

        if pending_task:
            actions.append({
                'category': 'LEARNING',
                'title': f"Practice: {pending_task.topic}",
                'description': pending_task.practice_task[:140] + ('...' if len(pending_task.practice_task) > 140 else ''),
                'badge': f"Week {pending_task.week_number}",
                'action_url': '/learning/',
                'completed': False
            })

        # 4. Profile completion check
        profile = getattr(user, 'profile', None)
        if profile and profile.completion_percentage < 80:
            actions.append({
                'category': 'PROFILE',
                'title': 'Complete Your Candidate Profile',
                'description': f"Your profile is currently at {profile.completion_percentage}%. Add your GitHub, LinkedIn, and project links to boost employer visibility.",
                'badge': 'Profile',
                'action_url': '/profile/',
                'completed': False
            })

        # 5. Check if user hasn't uploaded a resume
        if not user.resumes.exists():
            actions.append({
                'category': 'RESUME',
                'title': 'Upload Your Resume for Match Scoring',
                'description': 'Upload your PDF or DOCX resume to get your InternTrack Resume Match Score and ATS keyword analysis.',
                'badge': 'Essential',
                'action_url': '/resumes/',
                'completed': False
            })

        return Response({
            'today': today.isoformat(),
            'total_actions': len(actions),
            'actions': actions
        }, status=status.HTTP_200_OK)
