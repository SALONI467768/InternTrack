from django.urls import path
from .views import (
    ResumeListCreateView,
    ResumeDetailView,
    ResumeSetPrimaryView,
    ResumeTextAnalyzeView
)

urlpatterns = [
    path('', ResumeListCreateView.as_view(), name='resume-list-create'),
    path('<uuid:pk>/', ResumeDetailView.as_view(), name='resume-detail'),
    path('<uuid:pk>/set-primary/', ResumeSetPrimaryView.as_view(), name='resume-set-primary'),
    path('analyze-text/', ResumeTextAnalyzeView.as_view(), name='resume-text-analyze'),
]
