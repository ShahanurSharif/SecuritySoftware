from rest_framework import serializers
from .models import IncidentReport


class IncidentReportSerializer(serializers.ModelSerializer):
    reported_by_name = serializers.SerializerMethodField()
    branch_name = serializers.SerializerMethodField()
    net_loss = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = IncidentReport
        fields = [
            'id', 'reported_by', 'reported_by_name', 'branch', 'branch_name',
            'incident_date', 'incident_time',
            'amount_lost', 'amount_recovered', 'net_loss',
            'damaged_items', 'description',
            'police_intervention', 'injured',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_reported_by_name(self, obj):
        if obj.reported_by:
            name = f'{obj.reported_by.first_name} {obj.reported_by.last_name}'.strip()
            return name or obj.reported_by.username
        return ''

    def get_branch_name(self, obj):
        return obj.branch.name if obj.branch else ''
