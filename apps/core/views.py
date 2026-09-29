from rest_framework import views, permissions, status
from rest_framework.response import Response
from django.http import HttpResponse
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import ActivityLog
from services.report_service import build_career_report_data, generate_pdf_report
from services.ai import get_ai_provider

class CareerReportDataView(views.APIView):
    """
    GET /api/core/report/
    Returns structured career report data.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        report_data = build_career_report_data(request.user)
        return Response(report_data, status=status.HTTP_200_OK)

class CareerReportPdfView(views.APIView):
    """
    GET /api/core/report/pdf/
    Generates and downloads the professional PDF career report.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        report_data = build_career_report_data(request.user)
        try:
            pdf_bytes = generate_pdf_report(report_data)
            response = HttpResponse(pdf_bytes, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="InternTrack_Report_{request.user.id}.pdf"'
            ActivityLog.log_activity(request.user, 'REPORT_DOWNLOADED', 'Downloaded PDF career report')
            return response
        except Exception as e:
            return Response({'error': f'PDF generation failed: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class SystemHealthView(views.APIView):
    """
    GET /api/core/health/
    Health check verifying database connection, AI provider configuration, and system status.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        from django.db import connection
        db_ok = False
        try:
            connection.ensure_connection()
            db_ok = True
        except Exception:
            db_ok = False

        provider = get_ai_provider()
        provider_name = provider.__class__.__name__

        return Response({
            'status': 'healthy' if db_ok else 'degraded',
            'database': 'connected' if db_ok else 'disconnected',
            'ai_provider': provider_name,
            'version': '1.0.0',
            'product': 'InternTrack AI'
        }, status=status.HTTP_200_OK)

# ==============================================================================
# Frontend Template Views
# ==============================================================================

class LandingPageView(TemplateView):
    template_name = 'landing.html'

class LoginPageView(TemplateView):
    template_name = 'auth/login.html'

class RegisterPageView(TemplateView):
    template_name = 'auth/register.html'

class DashboardView(TemplateView):
    template_name = 'dashboard/index.html'

class ProfileView(TemplateView):
    template_name = 'dashboard/profile.html'

class ResumesView(TemplateView):
    template_name = 'dashboard/resumes.html'

class ResumeAnalyzeView(TemplateView):
    template_name = 'dashboard/resume_analyze.html'

class JobsView(TemplateView):
    template_name = 'dashboard/jobs.html'

class JobAddView(TemplateView):
    template_name = 'dashboard/job_add.html'

class JobDetailPageView(TemplateView):
    template_name = 'dashboard/job_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['job_id'] = kwargs.get('pk')
        return context

class ApplicationsView(TemplateView):
    template_name = 'dashboard/applications.html'

class ApplicationDetailView(TemplateView):
    template_name = 'dashboard/application_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['application_id'] = kwargs.get('pk')
        return context

class SkillsView(TemplateView):
    template_name = 'dashboard/skills.html'

class SkillGapView(TemplateView):
    template_name = 'dashboard/skill_gap.html'

class AnalyticsView(TemplateView):
    template_name = 'dashboard/analytics.html'

class InterviewsView(TemplateView):
    template_name = 'dashboard/interviews.html'

class LearningView(TemplateView):
    template_name = 'dashboard/learning.html'

class NotificationsView(TemplateView):
    template_name = 'dashboard/notifications.html'

class SettingsView(TemplateView):
    template_name = 'dashboard/settings.html'

class ReportsView(TemplateView):
    template_name = 'dashboard/reports.html'
