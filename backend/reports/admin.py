from django.contrib import admin
from .models import IncidentReport


@admin.register(IncidentReport)
class IncidentReportAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'branch', 'incident_date', 'incident_time',
        'amount_lost', 'amount_recovered', 'police_intervention', 'injured',
        'reported_by',
    )
    list_filter = ('police_intervention', 'injured', 'branch', 'incident_date')
    search_fields = ('description', 'damaged_items')
    date_hierarchy = 'incident_date'
    raw_id_fields = ('reported_by', 'branch')
