from django.contrib import admin
from .models import Attendance


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ['user', 'type', 'branch', 'captured_time', 'method', 'status', 'created_at']
    list_filter = ['type', 'method', 'status', 'branch']
    search_fields = ['user__first_name', 'user__last_name', 'branch__name', 'captured_branch']
    readonly_fields = ['created_at']
