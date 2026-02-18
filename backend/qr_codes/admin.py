from django.contrib import admin
from .models import QRCode, QRCodeSubmission


@admin.register(QRCode)
class QRCodeAdmin(admin.ModelAdmin):
    list_display = ['area_name', 'branch', 'status', 'created_at']
    list_filter = ['status', 'branch__company']
    search_fields = ['area_name', 'branch__name', 'branch__company__name']


@admin.register(QRCodeSubmission)
class QRCodeSubmissionAdmin(admin.ModelAdmin):
    list_display = ['qr_code', 'user', 'scanned_at']
    list_filter = ['qr_code__branch__company', 'qr_code']
    search_fields = ['qr_code__area_name', 'user__first_name', 'user__last_name']
