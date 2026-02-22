from django.contrib import admin
from .models import (
    ShiftTemplate, RosterShift, Availability,
    PTORequest, DropRequest, Notification,
)


@admin.register(ShiftTemplate)
class ShiftTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'branch', 'start_time', 'end_time', 'hourly_rate', 'break_duration_minutes', 'net_hours', 'color', 'is_active')
    list_filter = ('branch', 'is_active')
    search_fields = ('name', 'branch__name')

    @admin.display(description='Net Hours')
    def net_hours(self, obj):
        return f'{obj.net_hours}h'


@admin.register(RosterShift)
class RosterShiftAdmin(admin.ModelAdmin):
    list_display = ('user', 'branch', 'date', 'start_time', 'end_time', 'get_total_hours', 'hourly_rate', 'get_total_pay', 'status')
    list_filter = ('status', 'branch', 'date')
    search_fields = ('user__first_name', 'user__last_name', 'branch__name')
    date_hierarchy = 'date'

    @admin.display(description='Hours')
    def get_total_hours(self, obj):
        return f'{obj.total_hours}h'

    @admin.display(description='Pay')
    def get_total_pay(self, obj):
        return f'${obj.total_pay:.2f}'


@admin.register(Availability)
class AvailabilityAdmin(admin.ModelAdmin):
    list_display = ('user', 'date', 'preset', 'start_time', 'end_time', 'is_available', 'notes')
    list_filter = ('preset', 'is_available', 'date')
    search_fields = ('user__first_name', 'user__last_name')
    date_hierarchy = 'date'


@admin.register(PTORequest)
class PTORequestAdmin(admin.ModelAdmin):
    list_display = ('user', 'leave_type', 'start_date', 'end_date', 'status')
    list_filter = ('leave_type', 'status')
    search_fields = ('user__first_name', 'user__last_name')
    date_hierarchy = 'start_date'


@admin.register(DropRequest)
class DropRequestAdmin(admin.ModelAdmin):
    list_display = ('shift', 'requested_by', 'status', 'created_at')
    list_filter = ('status',)
    search_fields = ('requested_by__first_name', 'requested_by__last_name')


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'notification_type', 'channel', 'title', 'is_read', 'sent_at')
    list_filter = ('notification_type', 'channel', 'is_read')
    search_fields = ('user__first_name', 'user__last_name', 'title')
