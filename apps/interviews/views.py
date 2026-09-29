from rest_framework import generics, permissions, status, views
from rest_framework.response import Response
from django.db.models import Avg, Count
from .models import Interview, InterviewQuestion, InterviewAttempt
from .serializers import (
    InterviewSerializer,
    InterviewQuestionSerializer,
    InterviewAttemptSerializer
)
from apps.core.models import ActivityLog
from apps.notifications.models import Notification

class InterviewListCreateView(generics.ListCreateAPIView):
    """
    GET /api/interviews/ - List all interview logs for current user.
    POST /api/interviews/ - Schedule a new interview.
    """
    serializer_class = InterviewSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Interview.objects.filter(user=self.request.user).select_related('application__job')

    def perform_create(self, serializer):
        interview = serializer.save(user=self.request.user)
        # Advance application status to INTERVIEW if not already
        if interview.application.status != 'INTERVIEW':
            interview.application.update_status('INTERVIEW', notes=f"Interview scheduled for {interview.scheduled_at}")

        Notification.objects.create(
            user=self.request.user,
            title=f"Upcoming Interview: {interview.application.job.company}",
            message=f"You have a {interview.get_round_type_display()} scheduled for {interview.scheduled_at.strftime('%b %d, %Y at %H:%M')}.",
            notification_type='INTERVIEW_REMINDER',
            link=f"/interviews/"
        )

        ActivityLog.log_activity(
            self.request.user,
            'INTERVIEW_SCHEDULED',
            f"Scheduled {interview.get_round_type_display()} with {interview.application.job.company}"
        )

class InterviewDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET/PUT/PATCH/DELETE /api/interviews/<id>/
    """
    serializer_class = InterviewSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Interview.objects.filter(user=self.request.user)

    def perform_update(self, serializer):
        interview = serializer.save()
        if interview.result == 'PASSED':
            ActivityLog.log_activity(
                self.request.user,
                'INTERVIEW_PASSED',
                f"Passed {interview.get_round_type_display()} with {interview.application.job.company}!"
            )

class InterviewQuestionListView(generics.ListAPIView):
    """
    GET /api/interviews/questions/
    Browse interview practice catalog. Query params: category, difficulty, type.
    """
    serializer_class = InterviewQuestionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = InterviewQuestion.objects.all()
        category = self.request.query_params.get('category', '').strip()
        difficulty = self.request.query_params.get('difficulty', '').strip()
        q_type = self.request.query_params.get('type', '').strip()

        if category:
            queryset = queryset.filter(category__iexact=category)
        if difficulty:
            queryset = queryset.filter(difficulty__iexact=difficulty)
        if q_type:
            queryset = queryset.filter(question_type__iexact=q_type)

        return queryset

class InterviewAttemptCreateView(views.APIView):
    """
    POST /api/interviews/practice/submit/
    Submits a practice response, evaluates it against the model answer,
    and returns score + constructive feedback.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        question_id = request.data.get('question_id')
        user_answer = request.data.get('user_answer', '').strip()

        if not question_id or not user_answer:
            return Response({'error': 'question_id and user_answer are required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            question = InterviewQuestion.objects.get(pk=question_id)
        except InterviewQuestion.DoesNotExist:
            return Response({'error': 'Interview question not found.'}, status=status.HTTP_404_NOT_FOUND)

        # Evaluate score: compare keyword overlap between user answer and model answer
        model_words = set(re_word.lower() for re_word in question.model_answer.split() if len(re_word) > 3)
        user_words = set(re_word.lower() for re_word in user_answer.split() if len(re_word) > 3)

        if model_words:
            overlap = len(model_words.intersection(user_words))
            raw_pct = (overlap / len(model_words)) * 100
            # Normalize with length factor
            length_bonus = min(20.0, len(user_answer) / 10.0)
            score = round(min(100.0, max(25.0, (raw_pct * 0.8) + length_bonus)), 1)
        else:
            score = 75.0

        if score >= 80:
            feedback = "Excellent response! You captured the core technical concepts and articulated the rationale clearly."
        elif score >= 55:
            feedback = "Good foundation. Try expanding on practical edge cases and specific terminology mentioned in the model answer."
        else:
            feedback = "Keep practicing! Review the model explanation and emphasize specific architectural terms and mechanisms."

        attempt = InterviewAttempt.objects.create(
            user=request.user,
            question=question,
            user_answer=user_answer,
            score=score,
            feedback=feedback
        )

        ActivityLog.log_activity(
            request.user,
            'INTERVIEW_PRACTICE',
            f"Practiced question in {question.category} (Score: {score}%)"
        )

        return Response(InterviewAttemptSerializer(attempt).data, status=status.HTTP_201_CREATED)

class InterviewStatsView(views.APIView):
    """
    GET /api/interviews/stats/
    Returns summary statistics for the user's interview preparation and real interviews.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        interviews_qs = Interview.objects.filter(user=user)
        attempts_qs = InterviewAttempt.objects.filter(user=user)

        total_interviews = interviews_qs.count()
        upcoming = interviews_qs.filter(result='SCHEDULED').count()
        passed = interviews_qs.filter(result='PASSED').count()
        practice_count = attempts_qs.count()
        avg_score = attempts_qs.aggregate(avg=Avg('score'))['avg'] or 0.0

        return Response({
            'total_interviews': total_interviews,
            'upcoming_interviews': upcoming,
            'passed_interviews': passed,
            'practice_questions_attempted': practice_count,
            'average_practice_score': round(avg_score, 1)
        }, status=status.HTTP_200_OK)
