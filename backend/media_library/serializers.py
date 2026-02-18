import os
import mimetypes
from rest_framework import serializers
from .models import Media


class MediaSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = Media
        fields = ['id', 'file', 'file_url', 'file_type', 'name', 'mime_type', 'size',
                  'uploaded_by', 'content_type', 'object_id', 'created_at']
        read_only_fields = ['uploaded_by', 'mime_type', 'size', 'created_at']

    def get_file_url(self, obj):
        request = self.context.get('request')
        if obj.file and request:
            return request.build_absolute_uri(obj.file.url)
        return obj.file.url if obj.file else None

    def create(self, validated_data):
        request = self.context.get('request')
        uploaded_file = validated_data.get('file')

        # Auto-detect metadata
        if uploaded_file:
            if not validated_data.get('name'):
                validated_data['name'] = uploaded_file.name
            validated_data['size'] = uploaded_file.size
            mime, _ = mimetypes.guess_type(uploaded_file.name)
            validated_data['mime_type'] = mime or 'application/octet-stream'

            # Auto-detect file_type from mime if not provided or default
            if not validated_data.get('file_type') or validated_data['file_type'] == 'other':
                validated_data['file_type'] = self._detect_file_type(mime, uploaded_file.name)

        if request and request.user.is_authenticated:
            validated_data['uploaded_by'] = request.user

        return super().create(validated_data)

    @staticmethod
    def _detect_file_type(mime, filename):
        if not mime:
            ext = os.path.splitext(filename)[1].lower()
            if ext == '.pdf':
                return 'pdf'
            return 'other'

        if mime.startswith('image/'):
            return 'photo'
        if mime.startswith('video/'):
            return 'video'
        if mime.startswith('audio/'):
            return 'audio'
        if mime == 'application/pdf':
            return 'pdf'
        if mime.startswith('application/') or mime.startswith('text/'):
            return 'document'
        return 'other'
