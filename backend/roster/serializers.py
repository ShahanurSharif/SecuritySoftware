from django.utils import timezone
from rest_framework import serializers
from .models import (
    ShiftTemplate, RosterShift, Availability,
    PTORequest, DropRequest, Notification,
)


# ---------------------------------------------------------------------------
# Shift Template
# ---------------------------------------------------------------------------

class ShiftTemplateSerializer(serializers.ModelSerializer):
    branch_name = serializers.CharField(source='branch.name', read_only=True)
    duration_hours = serializers.FloatField(read_only=True)
    net_hours = serializers.FloatField(read_only=True)

    class Meta:
        model = ShiftTemplate
        fields = [
            'id', 'name', 'start_time', 'end_time',
            'branch', 'branch_name', 'color',
            'hourly_rate', 'break_duration_minutes',
            'duration_hours', 'net_hours',
            'is_active',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


# ---------------------------------------------------------------------------
# Roster Shift
# ---------------------------------------------------------------------------

class RosterShiftSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()
    branch_name = serializers.CharField(source='branch.name', read_only=True)
    template_name = serializers.CharField(source='template.name', read_only=True, default='')
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    created_by_name = serializers.SerializerMethodField()
    has_drop_request = serializers.SerializerMethodField()
    gross_hours = serializers.FloatField(read_only=True)
    total_hours = serializers.FloatField(read_only=True)
    total_pay = serializers.FloatField(read_only=True)

    class Meta:
        model = RosterShift
        fields = [
            'id', 'user', 'user_name',
            'branch', 'branch_name',
            'template', 'template_name',
            'date', 'start_time', 'end_time',
            'break_duration_minutes', 'hourly_rate',
            'gross_hours', 'total_hours', 'total_pay',
            'status', 'status_display', 'notes',
            'has_drop_request',
            'created_by', 'created_by_name',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']

    def get_user_name(self, obj):
        return f'{obj.user.first_name} {obj.user.last_name}'.strip() or obj.user.username

    def get_created_by_name(self, obj):
        if obj.created_by:
            return f'{obj.created_by.first_name} {obj.created_by.last_name}'.strip() or obj.created_by.username
        return ''

    def get_has_drop_request(self, obj):
        return obj.drop_requests.filter(status='pending').exists()

    def validate(self, data):
        """Run model-level overlap validation."""
        instance = RosterShift(**{**data, 'pk': self.instance.pk if self.instance else None})
        instance.clean()
        return data

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


# ---------------------------------------------------------------------------
# Availability
# ---------------------------------------------------------------------------

class AvailabilitySerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()
    preset_display = serializers.CharField(source='get_preset_display', read_only=True)

    class Meta:
        model = Availability
        fields = [
            'id', 'user', 'user_name',
            'date', 'preset', 'preset_display',
            'start_time', 'end_time', 'is_available',
            'notes',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_user_name(self, obj):
        return f'{obj.user.first_name} {obj.user.last_name}'.strip() or obj.user.username


# ---------------------------------------------------------------------------
# PTO Request
# ---------------------------------------------------------------------------

class PTORequestSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()
    type_display = serializers.CharField(source='get_leave_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    reviewed_by_name = serializers.SerializerMethodField()

    class Meta:
        model = PTORequest
        fields = [
            'id', 'user', 'user_name',
            'leave_type', 'type_display',
            'start_date', 'end_date', 'reason',
            'status', 'status_display',
            'reviewed_by', 'reviewed_by_name', 'reviewed_at', 'notes',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'reviewed_by', 'reviewed_at', 'created_at', 'updated_at']

    def get_user_name(self, obj):
        return f'{obj.user.first_name} {obj.user.last_name}'.strip() or obj.user.username

    def get_reviewed_by_name(self, obj):
        if obj.reviewed_by:
            return f'{obj.reviewed_by.first_name} {obj.reviewed_by.last_name}'.strip() or obj.reviewed_by.username
        return ''

    def validate(self, data):
        instance = PTORequest(**{**data, 'pk': self.instance.pk if self.instance else None})
        instance.clean()
        return data


# ---------------------------------------------------------------------------
# Drop Request
# ---------------------------------------------------------------------------

class DropRequestSerializer(serializers.ModelSerializer):
    requested_by_name = serializers.SerializerMethodField()
    reviewed_by_name = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    shift_detail = serializers.SerializerMethodField()

    class Meta:
        model = DropRequest
        fields = [
            'id', 'shift', 'shift_detail',
            'requested_by', 'requested_by_name',
            'reason', 'status', 'status_display',
            'reviewed_by', 'reviewed_by_name', 'reviewed_at',
            'created_at',
        ]
        read_only_fields = ['id', 'requested_by', 'reviewed_by', 'reviewed_at', 'created_at']

    def get_requested_by_name(self, obj):
        return f'{obj.requested_by.first_name} {obj.requested_by.last_name}'.strip() or obj.requested_by.username

    def get_reviewed_by_name(self, obj):
        if obj.reviewed_by:
            return f'{obj.reviewed_by.first_name} {obj.reviewed_by.last_name}'.strip() or obj.reviewed_by.username
        return ''

    def get_shift_detail(self, obj):
        s = obj.shift
        return {
            'id': s.id,
            'date': s.date,
            'start_time': s.start_time,
            'end_time': s.end_time,
            'branch_name': s.branch.name,
        }

    def create(self, validated_data):
        validated_data['requested_by'] = self.context['request'].user
        return super().create(validated_data)


# ---------------------------------------------------------------------------
# Notification
# ---------------------------------------------------------------------------

class NotificationSerializer(serializers.ModelSerializer):
    type_display = serializers.CharField(source='get_notification_type_display', read_only=True)
    channel_display = serializers.CharField(source='get_channel_display', read_only=True)

    class Meta:
        model = Notification
        fields = [
            'id', 'user', 'notification_type', 'type_display',
            'channel', 'channel_display',
            'title', 'message', 'is_read',
            'related_shift', 'sent_at',
        ]
        read_only_fields = ['id', 'sent_at']
