from django.contrib import admin
from .models import Interview, InterviewQuestion, InterviewAttempt

@admin.register(Interview)
class InterviewAdmin(admin.ModelAdmin):
    list_display = ('user', 'application', 'round_type', 'interview_type', 'scheduled_at', 'result')
    list_filter = ('round_type', 'result', 'scheduled_at')
    search_fields = ('user__email', 'application__job__company')

@admin.register(InterviewQuestion)
class InterviewQuestionAdmin(admin.ModelAdmin):
    list_display = ('category', 'question_type', 'difficulty', 'question_text')
    list_filter = ('category', 'question_type', 'difficulty')
    search_fields = ('question_text', 'model_answer')

@admin.register(InterviewAttempt)
class InterviewAttemptAdmin(admin.ModelAdmin):
    list_display = ('user', 'question', 'score', 'submitted_at')
    list_filter = ('score', 'submitted_at')
    search_fields = ('user__email', 'question__question_text')
