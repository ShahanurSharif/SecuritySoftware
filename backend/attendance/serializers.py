from rest_framework import serializers
from .models import Attendance


class AttendanceSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()
    branch_name = serializers.CharField(source='branch.name', read_only=True, default='')
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    method_display = serializers.CharField(source='get_method_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Attendance
        fields = [
            'id', 'user', 'user_name',
            'branch', 'branch_name',
            'type', 'type_display',
            'captured_time', 'captured_branch',
            'image', 'method', 'method_display',
            'status', 'status_display',
            'reason', 'notes',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']

    def get_user_name(self, obj):
        return f'{obj.user.first_name} {obj.user.last_name}'.strip() or obj.user.username


class AttendanceCreateSerializer(serializers.ModelSerializer):
    """Serializer used for creating attendance from camera/OCR."""

    class Meta:
        model = Attendance
        fields = [
            'branch', 'type', 'captured_time', 'captured_branch',
            'image', 'method', 'status', 'reason', 'notes',
        ]

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class OCRResultSerializer(serializers.Serializer):
    """Read-only serializer for OCR extraction results."""
    time = serializers.CharField()
    branch_name = serializers.CharField()
    raw_text = serializers.CharField()
