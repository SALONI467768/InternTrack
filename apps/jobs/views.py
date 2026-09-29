from rest_framework import generics, permissions, status, views
from rest_framework.response import Response
from django.db.models import Q
from .models import Job, JobSkill
from .serializers import (
    JobListSerializer,
    JobDetailSerializer,
    JobCreateFromTextSerializer
)
from apps.skills.models import Skill
from apps.core.models import ActivityLog
from services.ai import get_ai_provider
from services.match_engine import compute_job_match

class JobListCreateView(generics.ListCreateAPIView):
    """
    GET /api/jobs/ - List jobs tracked by the current user.
    POST /api/jobs/ - Manually create a job record.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return JobDetailSerializer
        return JobListSerializer

    def get_queryset(self):
        user = self.request.user
        queryset = Job.objects.filter(user=user)
        q = self.request.query_params.get('q', '').strip()
        job_type = self.request.query_params.get('type', '').strip()
        location = self.request.query_params.get('location', '').strip()

        if q:
            queryset = queryset.filter(Q(company__icontains=q) | Q(title__icontains=q))
        if job_type:
            queryset = queryset.filter(employment_type=job_type)
        if location:
            queryset = queryset.filter(location__icontains=location)

        return queryset

    def perform_create(self, serializer):
        job = serializer.save(user=self.request.user)
        ActivityLog.log_activity(self.request.user, 'JOB_ADDED', f"Added job {job.title} at {job.company}")

class JobParseAndCreateView(views.APIView):
    """
    POST /api/jobs/parse-and-create/
    Accepts raw pasted job description text, parses requirements via AI/NLP,
    creates the Job entity and links all detected JobSkills.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = JobCreateFromTextSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        raw_text = serializer.validated_data['raw_text']
        user_company = serializer.validated_data.get('company', '').strip()
        user_title = serializer.validated_data.get('title', '').strip()
        user_url = serializer.validated_data.get('job_url', '').strip()
        user_loc = serializer.validated_data.get('location', '').strip()
        user_type = serializer.validated_data.get('employment_type', 'INTERNSHIP')

        ai_provider = get_ai_provider()
        parsed = ai_provider.analyze_job_description(raw_text)

        # Merge user inputs with AI extracted information
        company = user_company or parsed.get('company') or "Target Company"
        title = user_title or parsed.get('title') or "Software Engineer"
        location = user_loc or parsed.get('location') or "Remote / Flexible"
        emp_type = user_type or parsed.get('employment_type') or "INTERNSHIP"

        job = Job.objects.create(
            user=request.user,
            company=company,
            title=title,
            job_url=user_url,
            location=location,
            employment_type=emp_type,
            experience_level=parsed.get('experience_level', 'Fresher / 0-1 Years'),
            education_requirement=parsed.get('education_requirements', ''),
            salary_range=parsed.get('salary_range', ''),
            raw_description=raw_text,
            parsed_requirements={
                'responsibilities': parsed.get('responsibilities', []),
                'required_skills': parsed.get('required_skills', []),
                'preferred_skills': parsed.get('preferred_skills', []),
            }
        )

        # Create or link skills
        required_skills = parsed.get('required_skills', [])
        preferred_skills = parsed.get('preferred_skills', [])

        for s_name in required_skills:
            skill, _ = Skill.objects.get_or_create(
                name=s_name,
                defaults={'category': 'FRAMEWORKS' if ' ' in s_name else 'LANGUAGES'}
            )
            JobSkill.objects.get_or_create(job=job, skill=skill, defaults={'is_critical': True})

        for s_name in preferred_skills:
            skill, _ = Skill.objects.get_or_create(
                name=s_name,
                defaults={'category': 'FRAMEWORKS' if ' ' in s_name else 'LANGUAGES'}
            )
            JobSkill.objects.get_or_create(job=job, skill=skill, defaults={'is_critical': False})

        # Optionally auto-create an Application in SAVED status
        from apps.applications.models import Application
        app, created = Application.objects.get_or_create(
            user=request.user,
            job=job,
            defaults={'status': 'SAVED', 'source': 'InternTrack Job Parser'}
        )

        ActivityLog.log_activity(
            request.user,
            'JOB_PARSED',
            f"Parsed and tracked role: {job.title} at {job.company}"
        )

        detail_serializer = JobDetailSerializer(job)
        return Response(detail_serializer.data, status=status.HTTP_201_CREATED)

class JobDetailView(generics.RetrieveDestroyAPIView):
    """
    GET /api/jobs/<id>/ - Retrieve complete job requirement details.
    DELETE /api/jobs/<id>/ - Remove job requirement.
    """
    serializer_class = JobDetailSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Job.objects.filter(user=self.request.user)

    def perform_destroy(self, instance):
        title = instance.title
        instance.delete()
        ActivityLog.log_activity(self.request.user, 'JOB_DELETED', f"Deleted job {title}")

class JobAnalyzeMatchView(views.APIView):
    """
    POST /api/jobs/<id>/analyze-match/
    Executes the Job Match Analyzer comparing user skills & resume against this job posting.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            job = Job.objects.get(pk=pk, user=request.user)
        except Job.DoesNotExist:
            return Response({'error': 'Job posting not found.'}, status=status.HTTP_404_NOT_FOUND)

        match_results = compute_job_match(request.user, job)
        return Response(match_results, status=status.HTTP_200_OK)

class JobGenerateCoverLetterView(views.APIView):
    """
    POST /api/jobs/<id>/generate-cover-letter/
    Generates a personalized, editable cover letter tailored to the job requirements.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            job = Job.objects.get(pk=pk, user=request.user)
        except Job.DoesNotExist:
            return Response({'error': 'Job posting not found.'}, status=status.HTTP_404_NOT_FOUND)

        user_skills = [us.skill.name for us in request.user.user_skills.select_related('skill')]
        profile_data = {
            'full_name': getattr(request.user.profile, 'full_name', 'Candidate'),
            'skills': user_skills,
            'target_role': getattr(request.user.profile, 'target_role', 'Software Developer'),
        }
        job_data = {
            'title': job.title,
            'company': job.company,
        }

        ai_provider = get_ai_provider()
        cover_letter = ai_provider.generate_cover_letter(profile_data, job_data)

        return Response({
            'cover_letter': cover_letter,
            'title': job.title,
            'company': job.company,
            'editable': True
        }, status=status.HTTP_200_OK)

class JobInterviewQuestionsView(views.APIView):
    """
    GET /api/jobs/<id>/interview-questions/
    Generates tailored interview practice questions matching this job's tech stack.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        try:
            job = Job.objects.get(pk=pk, user=request.user)
        except Job.DoesNotExist:
            return Response({'error': 'Job posting not found.'}, status=status.HTTP_404_NOT_FOUND)

        skills = [js.skill.name for js in job.job_skills.select_related('skill')]
        job_data = {'title': job.title, 'company': job.company}

        ai_provider = get_ai_provider()
        questions = ai_provider.generate_interview_questions(job_data, skills)
        return Response({'questions': questions}, status=status.HTTP_200_OK)
