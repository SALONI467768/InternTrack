from django.urls import path
from .views import (
    InterviewListCreateView,
    InterviewDetailView,
    InterviewQuestionListView,
    InterviewAttemptCreateView,
    InterviewStatsView
)

urlpatterns = [
    path('', InterviewListCreateView.as_view(), name='interview-list-create'),
    path('<uuid:pk>/', InterviewDetailView.as_view(), name='interview-detail'),
    path('questions/', InterviewQuestionListView.as_view(), name='interview-questions-list'),
    path('practice/submit/', InterviewAttemptCreateView.as_view(), name='interview-attempt-submit'),
    path('stats/', InterviewStatsView.as_view(), name='interview-stats'),
]
