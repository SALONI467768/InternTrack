from django.urls import path
from .views import (
    SkillListCreateView,
    UserSkillListCreateView,
    UserSkillDetailView,
    SkillIntelligenceView,
    SkillGapAnalysisView
)

urlpatterns = [
    path('', SkillListCreateView.as_view(), name='skill-list-create'),
    path('my-skills/', UserSkillListCreateView.as_view(), name='user-skill-list-create'),
    path('my-skills/<int:pk>/', UserSkillDetailView.as_view(), name='user-skill-detail'),
    path('intelligence/', SkillIntelligenceView.as_view(), name='skill-intelligence'),
    path('gap-analysis/', SkillGapAnalysisView.as_view(), name='skill-gap-analysis'),
]
