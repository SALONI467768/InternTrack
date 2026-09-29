import os
from rest_framework import generics, permissions, status, views
from rest_framework.response import Response
from .models import Resume, ResumeSkill
from .serializers import ResumeListSerializer, ResumeDetailSerializer, ResumeUploadSerializer
from apps.skills.models import Skill, UserSkill
from apps.core.models import ActivityLog
from services.resume_parser import process_and_analyze_resume
from services.ai import get_ai_provider

class ResumeListCreateView(generics.ListCreateAPIView):
    """
    GET /api/resumes/ - List all resumes uploaded by the authenticated user.
    POST /api/resumes/ - Upload, parse, and analyze a new resume document.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ResumeUploadSerializer
        return ResumeListSerializer

    def get_queryset(self):
        return Resume.objects.filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
        upload_serializer = ResumeUploadSerializer(data=request.data)
        upload_serializer.is_valid(raise_exception=True)

        uploaded_file = upload_serializer.validated_data['file']
        is_primary = upload_serializer.validated_data.get('is_primary', True)

        # Process and parse resume
        raw_text, analysis = process_and_analyze_resume(uploaded_file, uploaded_file.name)

        # Reset file pointer for model save
        uploaded_file.seek(0)

        # If this is the user's first resume, force is_primary=True
        if not Resume.objects.filter(user=request.user).exists():
            is_primary = True

        resume = Resume.objects.create(
            user=request.user,
            file=uploaded_file,
            file_name=uploaded_file.name,
            file_size=uploaded_file.size,
            raw_text=raw_text,
            is_primary=is_primary,
            match_score=analysis.get('match_score', 0.0),
            score_breakdown=analysis.get('score_breakdown', {}),
            extracted_data={
                'full_name': analysis.get('full_name', ''),
                'email': analysis.get('email', ''),
                'phone': analysis.get('phone', ''),
                'has_sections': analysis.get('has_sections', {}),
            },
            improvement_suggestions=analysis.get('improvement_suggestions', [])
        )

        # Link detected skills
        detected_skills = analysis.get('detected_skills', [])
        for skill_name in detected_skills:
            skill, _ = Skill.objects.get_or_create(
                name=skill_name,
                defaults={'category': 'FRAMEWORKS' if ' ' in skill_name else 'LANGUAGES'}
            )
            ResumeSkill.objects.get_or_create(resume=resume, skill=skill, defaults={'frequency': 1})
            
            # Optionally populate user skills if not already present
            UserSkill.objects.get_or_create(
                user=request.user,
                skill=skill,
                defaults={'proficiency': 'INTERMEDIATE', 'years_of_experience': 1.0}
            )

        # Update profile completion
        if hasattr(request.user, 'profile'):
            request.user.profile.calculate_completion()
            request.user.profile.save()

        ActivityLog.log_activity(
            request.user,
            'RESUME_UPLOADED',
            f"Uploaded resume {uploaded_file.name} (Match Score: {resume.match_score})"
        )

        detail_serializer = ResumeDetailSerializer(resume, context={'request': request})
        return Response(detail_serializer.data, status=status.HTTP_201_CREATED)

class ResumeDetailView(generics.RetrieveDestroyAPIView):
    """
    GET /api/resumes/<id>/ - Retrieve complete resume breakdown.
    DELETE /api/resumes/<id>/ - Remove resume.
    """
    serializer_class = ResumeDetailSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Resume.objects.filter(user=self.request.user)

    def perform_destroy(self, instance):
        file_name = instance.file_name
        instance.delete()
        ActivityLog.log_activity(self.request.user, 'RESUME_DELETED', f"Deleted resume {file_name}")

class ResumeSetPrimaryView(views.APIView):
    """
    POST /api/resumes/<id>/set-primary/
    Designates a specific resume as the user's primary document.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            resume = Resume.objects.get(pk=pk, user=request.user)
            resume.is_primary = True
            resume.save()
            return Response({'message': f"Resume '{resume.file_name}' set as primary."}, status=status.HTTP_200_OK)
        except Resume.DoesNotExist:
            return Response({'error': 'Resume not found.'}, status=status.HTTP_404_NOT_FOUND)

class ResumeTextAnalyzeView(views.APIView):
    """
    POST /api/resumes/analyze-text/
    Directly analyzes pasted resume text to generate an instant InternTrack Match Score.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        raw_text = request.data.get('text', '').strip()
        if not raw_text or len(raw_text) < 50:
            return Response({'error': 'Please provide sufficient resume text (at least 50 characters).'}, status=status.HTTP_400_BAD_REQUEST)

        ai_provider = get_ai_provider()
        analysis = ai_provider.parse_resume(raw_text)
        return Response(analysis, status=status.HTTP_200_OK)
