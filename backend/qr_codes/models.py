from django.db import models
from django.conf import settings
from branches.models import Branch


class QRCode(models.Model):
    STATUS_CHOICES = [
        ('Active', 'Active'),
        ('Inactive', 'Inactive'),
    ]

    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='qr_codes')
    area_name = models.CharField(max_length=255)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['branch__company__name', 'branch__name', 'area_name']
        unique_together = ('branch', 'area_name')
        indexes = [
            models.Index(fields=['branch', 'area_name']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f'{self.area_name} — {self.branch}'


class QRCodeSubmission(models.Model):
    """Pivot table: records each QR code scan by a user."""
    qr_code = models.ForeignKey(QRCode, on_delete=models.CASCADE, related_name='submissions')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='qr_submissions')
    scanned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-scanned_at']
        indexes = [
            models.Index(fields=['qr_code', '-scanned_at']),
            models.Index(fields=['user', '-scanned_at']),
        ]

    def __str__(self):
        return f'{self.user} scanned {self.qr_code} at {self.scanned_at}'
