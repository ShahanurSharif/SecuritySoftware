from rest_framework import viewsets, permissions, parsers
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from .models import Media
from .serializers import MediaSerializer


class MediaViewSet(viewsets.ModelViewSet):
    queryset = Media.objects.select_related('uploaded_by', 'content_type').all()
    serializer_class = MediaSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser, parsers.JSONParser]
    filterset_fields = ['file_type', 'content_type', 'object_id']
    search_fields = ['name', 'mime_type']
    ordering_fields = ['name', 'file_type', 'size', 'created_at']
    ordering = ['-created_at']
