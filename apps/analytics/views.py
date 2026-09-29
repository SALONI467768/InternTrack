from rest_framework import views, permissions, status
from rest_framework.response import Response
from django.db.models import Count, Avg, F
from django.db.models.functions import TruncMonth
from django.utils import timezone
from datetime import timedelta
from apps.applications.models import Application, ApplicationStatusHistory
from apps.jobs.models import Job, JobSkill
from apps.interviews.models import Interview
from apps.skills.models import UserSkill
from apps.core.models import ActivityLog
from services.ai import get_ai_provider

class DashboardAnalyticsView(views.APIView):
    """
    GET /api/analytics/dashboard/
    Calculates dynamic metrics, funnel conversions, and chart datasets directly from database records.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        applications = Application.objects.filter(user=user).select_related('job')
        total_apps = applications.count()

        # Status counts
        status_counts = dict(
            applications.values('status').annotate(count=Count('id')).values_list('status', 'count')
        )
        saved_count = status_counts.get('SAVED', 0)
        applied_count = status_counts.get('APPLIED', 0)
        assessment_count = status_counts.get('ASSESSMENT', 0)
        interview_count = status_counts.get('INTERVIEW', 0)
        offer_count = status_counts.get('OFFER', 0)
        rejected_count = status_counts.get('REJECTED', 0)
        withdrawn_count = status_counts.get('WITHDRAWN', 0)

        active_count = applied_count + assessment_count + interview_count
        progressed_count = assessment_count + interview_count + offer_count + rejected_count

        # Formulated Rates
        actioned_total = total_apps - saved_count
        if actioned_total > 0:
            response_rate = round((progressed_count / actioned_total) * 100, 1)
            interview_rate = round(((interview_count + offer_count) / actioned_total) * 100, 1)
            offer_rate = round((offer_count / actioned_total) * 100, 1)
        else:
            response_rate = 0.0
            interview_rate = 0.0
            offer_rate = 0.0

        # Average days to first response (from APPLIED to next status in history)
        transitions = ApplicationStatusHistory.objects.filter(
            application__user=user,
            from_status='APPLIED'
        ).select_related('application')

        diffs_days = []
        for t in transitions:
            if t.application.applied_date:
                diff = (t.changed_at.date() - t.application.applied_date).days
                if diff >= 0:
                    diffs_days.append(diff)

        avg_response_days = round(sum(diffs_days) / len(diffs_days), 1) if diffs_days else 0.0

        # Applications by Month (Last 6 Months)
        monthly_apps = (
            applications.annotate(month=TruncMonth('created_at'))
            .values('month')
            .annotate(count=Count('id'))
            .order_by('month')
        )
        monthly_labels = [m['month'].strftime('%b %Y') for m in monthly_apps if m['month']]
        monthly_values = [m['count'] for m in monthly_apps if m['month']]

        # Applications by Status Breakdown
        status_chart = {
            'labels': ['Saved', 'Applied', 'Assessment', 'Interview', 'Offer', 'Rejected', 'Withdrawn'],
            'data': [saved_count, applied_count, assessment_count, interview_count, offer_count, rejected_count, withdrawn_count]
        }

        # Top Roles Applied For
        role_counts = (
            applications.values('job__title')
            .annotate(count=Count('id'))
            .order_by('-count')[:5]
        )
        roles_chart = {
            'labels': [r['job__title'] for r in role_counts],
            'data': [r['count'] for r in role_counts]
        }

        # Top Companies Applied To
        company_counts = (
            applications.values('job__company')
            .annotate(count=Count('id'))
            .order_by('-count')[:5]
        )
        companies_chart = {
            'labels': [c['job__company'] for c in company_counts],
            'data': [c['count'] for c in company_counts]
        }

        # Application Funnel (Saved -> Applied -> Assessment -> Interview -> Offer)
        funnel = [
            {'stage': 'Tracked / Saved', 'count': total_apps, 'percentage': 100.0},
            {
                'stage': 'Applied',
                'count': total_apps - saved_count,
                'percentage': round(((total_apps - saved_count) / total_apps * 100), 1) if total_apps > 0 else 0
            },
            {
                'stage': 'Assessments',
                'count': assessment_count + interview_count + offer_count,
                'percentage': round(((assessment_count + interview_count + offer_count) / total_apps * 100), 1) if total_apps > 0 else 0
            },
            {
                'stage': 'Interviews',
                'count': interview_count + offer_count,
                'percentage': round(((interview_count + offer_count) / total_apps * 100), 1) if total_apps > 0 else 0
            },
            {
                'stage': 'Offers',
                'count': offer_count,
                'percentage': round((offer_count / total_apps * 100), 1) if total_apps > 0 else 0
            },
        ]

        return Response({
            'kpis': {
                'total_applications': total_apps,
                'active_applications': active_count,
                'interviews': interview_count,
                'offers': offer_count,
                'rejected': rejected_count,
                'response_rate': response_rate,
                'interview_rate': interview_rate,
                'offer_rate': offer_rate,
                'avg_response_days': avg_response_days,
            },
            'formulas': {
                'response_rate': '(Assessments + Interviews + Offers + Rejected) / Submitted Applications * 100',
                'interview_rate': '(Interviews + Offers) / Submitted Applications * 100',
                'offer_rate': 'Offers / Submitted Applications * 100',
            },
            'charts': {
                'monthly': {'labels': monthly_labels, 'data': monthly_values},
                'status': status_chart,
                'roles': roles_chart,
                'companies': companies_chart,
                'funnel': funnel,
            }
        }, status=status.HTTP_200_OK)

class CareerInsightsView(views.APIView):
    """
    GET /api/analytics/insights/
    Returns explainable AI-generated career intelligence based strictly on real user applications and jobs.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        user_skills = [us.skill.name for us in user.user_skills.select_related('skill')]
        
        user_data = {
            'skills': user_skills,
            'target_role': getattr(user.profile, 'target_role', 'Software Developer') if hasattr(user, 'profile') else 'Developer',
        }

        # Tracked jobs
        jobs = Job.objects.filter(user=user)
        tracked_jobs_data = []
        for j in jobs:
            skills = [js.skill.name for js in j.job_skills.select_related('skill') if js.is_critical]
            tracked_jobs_data.append({
                'title': j.title,
                'company': j.company,
                'required_skills': skills
            })

        ai_provider = get_ai_provider()
        insights = ai_provider.generate_career_insights(user_data, tracked_jobs_data)

        return Response({
            'total_jobs_analyzed': len(tracked_jobs_data),
            'candidate_skills_count': len(user_skills),
            'insights': insights
        }, status=status.HTTP_200_OK)

class ActivityLogListView(views.APIView):
    """
    GET /api/analytics/activity/
    Returns recent activity timeline for the user.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        logs = ActivityLog.objects.filter(user=request.user)[:30]
        data = [
            {
                'id': str(log.id),
                'action': log.action,
                'details': log.details,
                'created_at': log.created_at.strftime('%b %d, %Y %H:%M')
            }
            for log in logs
        ]
        return Response({'logs': data}, status=status.HTTP_200_OK)
