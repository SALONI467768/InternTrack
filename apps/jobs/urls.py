from django.urls import path
from .views import (
    JobListCreateView,
    JobParseAndCreateView,
    JobDetailView,
    JobAnalyzeMatchView,
    JobGenerateCoverLetterView,
    JobInterviewQuestionsView
)

urlpatterns = [
    path('', JobListCreateView.as_view(), name='job-list-create'),
    path('parse-and-create/', JobParseAndCreateView.as_view(), name='job-parse-and-create'),
    path('<uuid:pk>/', JobDetailView.as_view(), name='job-detail'),
    path('<uuid:pk>/analyze-match/', JobAnalyzeMatchView.as_view(), name='job-analyze-match'),
    path('<uuid:pk>/generate-cover-letter/', JobGenerateCoverLetterView.as_view(), name='job-generate-cover-letter'),
    path('<uuid:pk>/interview-questions/', JobInterviewQuestionsView.as_view(), name='job-interview-questions'),
]
