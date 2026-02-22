from rest_framework import viewsets, permissions
from django_filters import rest_framework as django_filters
from .models import IncidentReport
from .serializers import IncidentReportSerializer


class IncidentReportFilter(django_filters.FilterSet):
    date_from = django_filters.DateFilter(field_name='incident_date', lookup_expr='gte')
    date_to = django_filters.DateFilter(field_name='incident_date', lookup_expr='lte')

    class Meta:
        model = IncidentReport
        fields = ['reported_by', 'branch', 'date_from', 'date_to', 'police_intervention', 'injured']


class IncidentReportViewSet(viewsets.ModelViewSet):
    """CRUD for incident reports."""
    queryset = IncidentReport.objects.select_related('reported_by', 'branch').all()
    serializer_class = IncidentReportSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_class = IncidentReportFilter
    ordering_fields = ['incident_date', 'incident_time', 'amount_lost', 'created_at']
    ordering = ['-incident_date', '-incident_time']

    def perform_create(self, serializer):
        serializer.save(reported_by=self.request.user)
