from django.urls import path
from .views import (
    ApplicationListCreateView,
    ApplicationDetailView,
    ApplicationUpdateStatusView,
    FollowUpListCreateView,
    FollowUpDetailView
)

urlpatterns = [
    path('', ApplicationListCreateView.as_view(), name='application-list-create'),
    path('<uuid:pk>/', ApplicationDetailView.as_view(), name='application-detail'),
    path('<uuid:pk>/update-status/', ApplicationUpdateStatusView.as_view(), name='application-update-status'),
    path('follow-ups/', FollowUpListCreateView.as_view(), name='followup-list-create'),
    path('follow-ups/<uuid:pk>/', FollowUpDetailView.as_view(), name='followup-detail'),
]
