from django.urls import path
from .views import ProfileDetailUpdateView

urlpatterns = [
    path('', ProfileDetailUpdateView.as_view(), name='profile-detail-update'),
]
