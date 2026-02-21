from django.db import models
from django.conf import settings
from branches.models import Branch


class Attendance(models.Model):
    TYPE_CHOICES = [
        ('clock_in', 'Clock In'),
        ('clock_out', 'Clock Out'),
    ]
    METHOD_CHOICES = [
        ('camera', 'Camera'),
        ('manual', 'Manual'),
    ]
    STATUS_CHOICES = [
        ('approved', 'Approved'),
        ('pending', 'Pending'),
        ('rejected', 'Rejected'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='attendances',
    )
    branch = models.ForeignKey(
        Branch,
        on_delete=models.CASCADE,
        related_name='attendances',
        null=True,
        blank=True,
    )
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    captured_time = models.CharField(
        max_length=20,
        blank=True,
        default='',
        help_text='Time extracted from OCR (HH:MM or HH:MM:SS)',
    )
    captured_branch = models.CharField(
        max_length=255,
        blank=True,
        default='',
        help_text='Branch/location name extracted from OCR',
    )
    image = models.ImageField(
        upload_to='attendance/%Y/%m/',
        blank=True,
        null=True,
        help_text='Photo captured from the attendance terminal',
    )
    method = models.CharField(max_length=10, choices=METHOD_CHOICES, default='camera')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='approved')
    reason = models.TextField(
        blank=True,
        default='',
        help_text='Reason for manual attendance request',
    )
    notes = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['branch', '-created_at']),
            models.Index(fields=['type']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f'{self.user} — {self.get_type_display()} at {self.created_at}'
