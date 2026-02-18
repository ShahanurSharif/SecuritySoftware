from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.contenttypes.models import ContentType
from media_library.models import Media
from media_library.serializers import MediaSerializer
from .models import Profile
from .serializers import ProfileSerializer, RoleSerializer, ChangePasswordSerializer


class ProfileViewSet(viewsets.ModelViewSet):
    queryset = Profile.objects.select_related('user', 'address', 'photo').all()
    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'user_id'
    lookup_url_kwarg = 'pk'
    search_fields = ['user__first_name', 'user__last_name', 'user__email', 'phone', 'group', 'role']
    ordering_fields = ['user__first_name', 'user__last_name', 'user__email', 'role', 'group', 'status', 'user__last_login']
    ordering = ['user__first_name', 'user__last_name']

    def perform_destroy(self, instance):
        """Delete the User (cascades to Profile)."""
        instance.user.delete()

    @action(detail=True, methods=['patch'], url_path='role')
    def change_role(self, request, pk=None):
        """Dedicated endpoint to change a user's role."""
        profile = self.get_object()
        serializer = RoleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        profile.role = serializer.validated_data['role']
        profile.save(update_fields=['role'])
        return Response(ProfileSerializer(profile, context={'request': request}).data)

    @action(detail=True, methods=['patch'], url_path='password')
    def change_password(self, request, pk=None):
        """Change a user's password."""
        profile = self.get_object()
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        profile.user.set_password(serializer.validated_data['password'])
        profile.user.save()
        return Response({'detail': 'Password updated successfully.'})

    @action(detail=True, methods=['get'], url_path='detail')
    def full_detail(self, request, pk=None):
        """Return full profile with all linked media."""
        profile = self.get_object()
        profile_data = ProfileSerializer(profile, context={'request': request}).data
        # Fetch all media linked to this profile
        ct = ContentType.objects.get_for_model(Profile)
        media_qs = Media.objects.filter(content_type=ct, object_id=profile.pk).order_by('-created_at')
        profile_data['media'] = MediaSerializer(media_qs, many=True, context={'request': request}).data
        return Response(profile_data)
