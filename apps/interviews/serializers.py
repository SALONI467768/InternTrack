from rest_framework import serializers
from .models import Interview, InterviewQuestion, InterviewAttempt

class InterviewSerializer(serializers.ModelSerializer):
    company = serializers.CharField(source='application.job.company', read_only=True)
    job_title = serializers.CharField(source='application.job.title', read_only=True)
    round_display = serializers.CharField(source='get_round_type_display', read_only=True)
    result_display = serializers.CharField(source='get_result_display', read_only=True)

    class Meta:
        model = Interview
        fields = (
            'id', 'application', 'company', 'job_title', 'round_type', 'round_display',
            'interview_type', 'scheduled_at', 'meeting_link',
            'questions_asked', 'feedback', 'result', 'result_display', 'created_at'
        )
        read_only_fields = ('id', 'created_at')

class InterviewQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = InterviewQuestion
        fields = ('id', 'category', 'question_type', 'difficulty', 'question_text', 'model_answer', 'explanation')

class InterviewAttemptSerializer(serializers.ModelSerializer):
    question_text = serializers.CharField(source='question.question_text', read_only=True)
    category = serializers.CharField(source='question.category', read_only=True)
    model_answer = serializers.CharField(source='question.model_answer', read_only=True)
    explanation = serializers.CharField(source='question.explanation', read_only=True)

    class Meta:
        model = InterviewAttempt
        fields = (
            'id', 'question', 'question_text', 'category', 'user_answer',
            'score', 'feedback', 'model_answer', 'explanation', 'submitted_at'
        )
        read_only_fields = ('id', 'score', 'feedback', 'submitted_at')
