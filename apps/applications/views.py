from rest_framework import generics, permissions, status, views
from rest_framework.response import Response
from django.db.models import Q
from django.utils import timezone
from .models import Application, ApplicationStatusHistory, FollowUp
from .serializers import (
    ApplicationListSerializer,
    ApplicationDetailSerializer,
    ApplicationCreateSerializer,
    ApplicationStatusUpdateSerializer,
    FollowUpSerializer
)
from apps.core.models import ActivityLog
from apps.notifications.models import Notification

class ApplicationListCreateView(generics.ListCreateAPIView):
    """
    GET /api/applications/ - List all tracked applications with search and filters.
    POST /api/applications/ - Create a new application tracker entry.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ApplicationCreateSerializer
        return ApplicationListSerializer

    def get_queryset(self):
        user = self.request.user
        queryset = Application.objects.filter(user=user).select_related('job')
        
        status_param = self.request.query_params.get('status', '').strip()
        search_param = self.request.query_params.get('q', '').strip()
        job_type = self.request.query_params.get('job_type', '').strip()
        location = self.request.query_params.get('location', '').strip()

        if status_param:
            queryset = queryset.filter(status=status_param)
        if search_param:
            queryset = queryset.filter(
                Q(job__company__icontains=search_param) |
                Q(job__title__icontains=search_param)
            )
        if job_type:
            queryset = queryset.filter(job__employment_type=job_type)
        if location:
            queryset = queryset.filter(job__location__icontains=location)

        return queryset

    def perform_create(self, serializer):
        application = serializer.save(user=self.request.user)
        # Record initial status in history
        ApplicationStatusHistory.objects.create(
            application=application,
            from_status='NONE',
            to_status=application.status,
            notes='Application tracked'
        )
        ActivityLog.log_activity(
            self.request.user,
            'APPLICATION_CREATED',
            f"Tracked application for {application.job.title} at {application.job.company}"
        )

class ApplicationDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET/PUT/PATCH/DELETE /api/applications/<id>/
    """
    serializer_class = ApplicationDetailSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Application.objects.filter(user=self.request.user).select_related('job')

    def perform_destroy(self, instance):
        company = instance.job.company
        title = instance.job.title
        instance.delete()
        ActivityLog.log_activity(self.request.user, 'APPLICATION_DELETED', f"Deleted application for {title} at {company}")

class ApplicationUpdateStatusView(views.APIView):
    """
    POST /api/applications/<id>/update-status/
    Transitions an application's status and updates the audit history timeline.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            application = Application.objects.get(pk=pk, user=request.user)
        except Application.DoesNotExist:
            return Response({'error': 'Application not found.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = ApplicationStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        new_status = serializer.validated_data['status']
        notes = serializer.validated_data.get('notes', '')

        old_status = application.status
        application.update_status(new_status, notes=notes)

        # Trigger notification if advancing to assessment or interview
        if new_status in ['ASSESSMENT', 'INTERVIEW', 'OFFER']:
            Notification.objects.create(
                user=request.user,
                title=f"Application Status Updated: {application.job.company}",
                message=f"Your application for {application.job.title} moved from {old_status} to {new_status}!",
                notification_type='APPLICATION_UPDATE' if new_status != 'INTERVIEW' else 'INTERVIEW_REMINDER',
                link=f"/applications/{application.id}/"
            )

        ActivityLog.log_activity(
            request.user,
            'APPLICATION_STATUS_CHANGED',
            f"Changed {application.job.company} status: {old_status} -> {new_status}"
        )

        detail_serializer = ApplicationDetailSerializer(application)
        return Response(detail_serializer.data, status=status.HTTP_200_OK)

class FollowUpListCreateView(generics.ListCreateAPIView):
    """
    GET /api/applications/follow-ups/ - List all follow-up reminders.
    POST /api/applications/follow-ups/ - Schedule a new follow-up.
    """
    serializer_class = FollowUpSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        queryset = FollowUp.objects.filter(user=user).select_related('application__job')
        filter_type = self.request.query_params.get('filter', '').strip()
        today = timezone.localdate()

        if filter_type == 'upcoming':
            queryset = queryset.filter(is_completed=False, follow_up_date__gte=today)
        elif filter_type == 'overdue':
            queryset = queryset.filter(is_completed=False, follow_up_date__lt=today)
        elif filter_type == 'pending':
            queryset = queryset.filter(is_completed=False)

        return queryset

    def perform_create(self, serializer):
        follow_up = serializer.save(user=self.request.user)
        ActivityLog.log_activity(
            self.request.user,
            'FOLLOW_UP_SCHEDULED',
            f"Scheduled follow-up for {follow_up.application.job.company} on {follow_up.follow_up_date}"
        )

class FollowUpDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET/PUT/PATCH/DELETE /api/applications/follow-ups/<id>/
    """
    serializer_class = FollowUpSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return FollowUp.objects.filter(user=self.request.user)
