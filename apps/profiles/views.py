from rest_framework import generics, permissions, status
from rest_framework.response import Response
from .models import Profile
from .serializers import ProfileSerializer
from apps.core.models import ActivityLog

class ProfileDetailUpdateView(generics.RetrieveUpdateAPIView):
    """
    GET /api/profile/
    Retrieve authenticated user's profile.

    PUT/PATCH /api/profile/
    Update user profile data and recalculate completion rate.
    """
    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        profile, _ = Profile.objects.get_or_create(user=self.request.user)
        profile.calculate_completion()
        return profile

    def perform_update(self, serializer):
        profile = serializer.save()
        profile.calculate_completion()
        profile.save()
        ActivityLog.log_activity(self.request.user, 'PROFILE_UPDATED', 'Updated developer profile details')
