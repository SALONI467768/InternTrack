from django.urls import path
from .views import (
    LearningRoadmapView,
    LearningRoadmapRegenerateView,
    LearningTaskUpdateView,
    SmartDailyActionsView
)

urlpatterns = [
    path('roadmap/', LearningRoadmapView.as_view(), name='learning-roadmap'),
    path('roadmap/regenerate/', LearningRoadmapRegenerateView.as_view(), name='learning-roadmap-regenerate'),
    path('tasks/<uuid:pk>/', LearningTaskUpdateView.as_view(), name='learning-task-update'),
    path('daily-actions/', SmartDailyActionsView.as_view(), name='smart-daily-actions'),
]
