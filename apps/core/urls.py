from django.urls import path
from .views import (
    CareerReportDataView,
    CareerReportPdfView,
    SystemHealthView
)

urlpatterns = [
    path('report/', CareerReportDataView.as_view(), name='core-report-data'),
    path('report/pdf/', CareerReportPdfView.as_view(), name='core-report-pdf'),
    path('health/', SystemHealthView.as_view(), name='core-health'),
]
