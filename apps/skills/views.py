from rest_framework import generics, permissions, status, views
from rest_framework.response import Response
from django.db.models import Q, Count
from .models import Skill, UserSkill
from .serializers import SkillSerializer, UserSkillSerializer
from apps.jobs.models import Job, JobSkill
from apps.core.models import ActivityLog

class SkillListCreateView(generics.ListCreateAPIView):
    """
    GET /api/skills/
    List or search available skills by keyword or category.
    POST /api/skills/
    Add a new skill into the taxonomy.
    """
    serializer_class = SkillSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = Skill.objects.all()
        query = self.request.query_params.get('q', '').strip()
        category = self.request.query_params.get('category', '').strip()

        if query:
            queryset = queryset.filter(Q(name__icontains=query) | Q(aliases__icontains=query))
        if category:
            queryset = queryset.filter(category=category)

        return queryset

class UserSkillListCreateView(generics.ListCreateAPIView):
    """
    GET /api/skills/my-skills/
    Retrieve all skills attached to the current user's profile.
    POST /api/skills/my-skills/
    Add or update a skill proficiency for the current user.
    """
    serializer_class = UserSkillSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return UserSkill.objects.filter(user=self.request.user).select_related('skill')

    def perform_create(self, serializer):
        user_skill = serializer.save()
        ActivityLog.log_activity(
            self.request.user,
            'SKILL_ADDED',
            f"Added skill {user_skill.skill.name} ({user_skill.proficiency})"
        )

class UserSkillDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET/PUT/PATCH/DELETE /api/skills/my-skills/<id>/
    Manage an individual user skill.
    """
    serializer_class = UserSkillSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return UserSkill.objects.filter(user=self.request.user)

    def perform_destroy(self, instance):
        skill_name = instance.skill.name
        user = self.request.user
        instance.delete()
        if hasattr(user, 'profile'):
            user.profile.calculate_completion()
            user.profile.save()
        ActivityLog.log_activity(user, 'SKILL_REMOVED', f"Removed skill {skill_name}")

class SkillIntelligenceView(views.APIView):
    """
    GET /api/skills/intelligence/
    Aggregates skill frequencies across all jobs tracked by the user,
    contrasting user skills with market demand.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        user_skills_qs = UserSkill.objects.filter(user=user).select_related('skill')
        user_skill_names = {us.skill.name.lower(): us.skill.name for us in user_skills_qs}

        # Jobs tracked by user
        tracked_jobs = Job.objects.filter(user=user)
        total_tracked_jobs = tracked_jobs.count()

        if total_tracked_jobs == 0:
            # Fallback to system-wide jobs or default baseline if user hasn't added jobs yet
            tracked_jobs = Job.objects.all()
            total_tracked_jobs = tracked_jobs.count()

        # Skill frequency across tracked jobs
        job_skills = (
            JobSkill.objects.filter(job__in=tracked_jobs)
            .values('skill__name', 'skill__category')
            .annotate(job_count=Count('job', distinct=True))
            .order_by('-job_count')
        )

        most_requested = []
        coverage_matched = []
        coverage_missing = []

        for item in job_skills:
            skill_name = item['skill__name']
            count = item['job_count']
            pct = round((count / total_tracked_jobs) * 100, 1) if total_tracked_jobs > 0 else 0

            skill_stat = {
                'skill': skill_name,
                'category': item['skill__category'],
                'jobs_count': count,
                'demand_percentage': pct,
                'user_has_skill': skill_name.lower() in user_skill_names
            }
            most_requested.append(skill_stat)

            if skill_name.lower() in user_skill_names:
                coverage_matched.append(skill_stat)
            else:
                coverage_missing.append(skill_stat)

        # Categorize coverage tiers
        coverage_pct = round((len(coverage_matched) / len(most_requested) * 100), 1) if most_requested else 0
        if coverage_pct >= 70:
            coverage_tier = 'High Coverage'
        elif coverage_pct >= 40:
            coverage_tier = 'Medium Coverage'
        else:
            coverage_tier = 'Low Coverage'

        return Response({
            'total_tracked_jobs': total_tracked_jobs,
            'total_market_skills_detected': len(most_requested),
            'user_skills_count': len(user_skill_names),
            'coverage_percentage': coverage_pct,
            'coverage_tier': coverage_tier,
            'most_requested_skills': most_requested[:15],
            'matched_skills': coverage_matched,
            'missing_skills': coverage_missing[:15],
            'disclaimer': 'Insights derived exclusively from the jobs you have tracked in InternTrack AI.'
        }, status=status.HTTP_200_OK)

class SkillGapAnalysisView(views.APIView):
    """
    GET /api/skills/gap-analysis/
    Calculates Critical, Important, and Optional skill gaps by comparing
    user profile & skills against the user's tracked job requirements.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        user_skills_qs = UserSkill.objects.filter(user=user).select_related('skill')
        user_skill_set = {us.skill.name.lower() for us in user_skills_qs}

        # Jobs tracked by user
        tracked_jobs = Job.objects.filter(user=user)
        total_jobs = tracked_jobs.count()

        if total_jobs == 0:
            tracked_jobs = Job.objects.all()
            total_jobs = tracked_jobs.count()

        job_skills = (
            JobSkill.objects.filter(job__in=tracked_jobs)
            .values('skill__name', 'skill__category', 'is_critical')
            .annotate(freq=Count('job', distinct=True))
            .order_by('-freq')
        )

        critical_gaps = []
        important_gaps = []
        optional_gaps = []
        matched = []

        for item in job_skills:
            s_name = item['skill__name']
            s_name_lower = s_name.lower()
            freq = item['freq']
            percentage = round((freq / total_jobs) * 100, 1) if total_jobs > 0 else 0
            is_critical = item['is_critical'] or percentage >= 50.0

            skill_entry = {
                'skill': s_name,
                'category': item['skill__category'],
                'market_frequency': freq,
                'market_percentage': percentage,
            }

            if s_name_lower in user_skill_set:
                matched.append(skill_entry)
            else:
                if is_critical or percentage >= 50.0:
                    critical_gaps.append(skill_entry)
                elif percentage >= 20.0:
                    important_gaps.append(skill_entry)
                else:
                    optional_gaps.append(skill_entry)

        target_role = getattr(user.profile, 'target_role', 'Software Developer') if hasattr(user, 'profile') else 'Developer'

        # Generate rule-based recommendations
        recommendations = []
        if critical_gaps:
            top_critical = [g['skill'] for g in critical_gaps[:3]]
            recommendations.append(
                f"Prioritize learning {', '.join(top_critical)}, which appear in over 50% of your target {target_role} roles."
            )
        if important_gaps:
            top_important = [g['skill'] for g in important_gaps[:3]]
            recommendations.append(
                f"Enhance your competitiveness by building mini-projects featuring {', '.join(top_important)}."
            )
        if not critical_gaps and matched:
            recommendations.append(
                "Great job! Your profile covers the primary critical requirements for your tracked roles. Focus on portfolio projects and interview preparation."
            )

        return Response({
            'target_role': target_role,
            'total_jobs_analyzed': total_jobs,
            'summary': {
                'matched_count': len(matched),
                'critical_count': len(critical_gaps),
                'important_count': len(important_gaps),
                'optional_count': len(optional_gaps),
            },
            'critical_gaps': critical_gaps,
            'important_gaps': important_gaps,
            'optional_gaps': optional_gaps,
            'matched_skills': matched,
            'actionable_recommendations': recommendations
        }, status=status.HTTP_200_OK)
