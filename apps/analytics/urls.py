from django.urls import path
from .views import (
    DashboardAnalyticsView,
    CareerInsightsView,
    ActivityLogListView
)

urlpatterns = [
    path('dashboard/', DashboardAnalyticsView.as_view(), name='analytics-dashboard'),
    path('insights/', CareerInsightsView.as_view(), name='analytics-insights'),
    path('activity/', ActivityLogListView.as_view(), name='analytics-activity'),
]
