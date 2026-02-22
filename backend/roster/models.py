from datetime import datetime, timedelta

from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from branches.models import Branch


# ---------------------------------------------------------------------------
# Shift Template — reusable shift definitions
# ---------------------------------------------------------------------------

class ShiftTemplate(models.Model):
    """Reusable shift definitions (e.g. Morning, Afternoon, Night)."""
    name = models.CharField(max_length=100)
    start_time = models.TimeField()
    end_time = models.TimeField()
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='shift_templates')
    color = models.CharField(max_length=7, default='#3B82F6', help_text='Hex color for calendar display')
    hourly_rate = models.DecimalField(max_digits=8, decimal_places=2, default=0, help_text='Default hourly rate ($)')
    break_duration_minutes = models.PositiveIntegerField(default=0, help_text='Unpaid break duration in minutes')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['branch', 'start_time']
        unique_together = ('branch', 'name')

    @property
    def duration_hours(self):
        """Gross shift duration in hours (before break deduction)."""
        d1 = datetime.combine(datetime.min, self.start_time)
        d2 = datetime.combine(datetime.min, self.end_time)
        delta = (d2 - d1).total_seconds() / 3600
        return round(delta, 2) if delta > 0 else round(delta + 24, 2)

    @property
    def net_hours(self):
        """Net billable hours (gross − break)."""
        return round(self.duration_hours - (self.break_duration_minutes / 60), 2)

    def __str__(self):
        return f'{self.name} ({self.start_time:%H:%M}–{self.end_time:%H:%M}) {self.net_hours}h @ {self.branch.name}'


# ---------------------------------------------------------------------------
# Roster Shift — actual assigned shift on a date
# ---------------------------------------------------------------------------

class RosterShift(models.Model):
    """A shift assigned to a user on a specific date at a branch."""
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('confirmed', 'Confirmed'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('no_show', 'No Show'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='roster_shifts')
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='roster_shifts')
    template = models.ForeignKey(ShiftTemplate, on_delete=models.SET_NULL, null=True, blank=True, related_name='roster_shifts')
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    break_duration_minutes = models.PositiveIntegerField(default=0, help_text='Unpaid break in minutes')
    hourly_rate = models.DecimalField(max_digits=8, decimal_places=2, default=0, help_text='Hourly rate ($)')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    notes = models.TextField(blank=True, default='')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_shifts')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['date', 'start_time']
        indexes = [
            models.Index(fields=['user', 'date']),
            models.Index(fields=['branch', 'date']),
            models.Index(fields=['date', 'status']),
        ]

    @property
    def gross_hours(self):
        """Gross shift duration in hours."""
        d1 = datetime.combine(datetime.min, self.start_time)
        d2 = datetime.combine(datetime.min, self.end_time)
        delta = (d2 - d1).total_seconds() / 3600
        return round(delta, 2) if delta > 0 else round(delta + 24, 2)

    @property
    def total_hours(self):
        """Net billable hours (gross − break)."""
        return round(self.gross_hours - (self.break_duration_minutes / 60), 2)

    @property
    def total_pay(self):
        """Total pay = net hours × hourly rate."""
        return round(float(self.total_hours) * float(self.hourly_rate), 2)

    def __str__(self):
        return f'{self.user.get_full_name()} — {self.date} {self.start_time:%H:%M}–{self.end_time:%H:%M} ({self.total_hours}h)'

    def clean(self):
        """Validate no overlapping shifts for the same user on the same date."""
        if self.start_time and self.end_time and self.start_time >= self.end_time:
            raise ValidationError('End time must be after start time.')

        overlapping = RosterShift.objects.filter(
            user=self.user,
            date=self.date,
            status__in=('scheduled', 'confirmed'),
        ).exclude(pk=self.pk).filter(
            start_time__lt=self.end_time,
            end_time__gt=self.start_time,
        )
        if overlapping.exists():
            raise ValidationError(
                f'Conflict: {self.user.get_full_name()} already has a shift '
                f'on {self.date} that overlaps with {self.start_time:%H:%M}–{self.end_time:%H:%M}.'
            )


# ---------------------------------------------------------------------------
# Availability — date-specific LPO availability with presets
# ---------------------------------------------------------------------------

class Availability(models.Model):
    """LPO user availability for specific dates with shortcut presets."""
    PRESET_CHOICES = [
        ('whole_day', 'Whole Day'),
        ('day_only', 'Day Only'),
        ('night_only', 'Night Only'),
        ('custom', 'Custom'),
    ]
    PRESET_TIMES = {
        'whole_day': ('00:00', '23:59'),
        'day_only': ('06:00', '18:00'),
        'night_only': ('18:00', '06:00'),
    }

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='availabilities')
    date = models.DateField(help_text='Specific date for availability')
    preset = models.CharField(max_length=20, choices=PRESET_CHOICES, default='custom')
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_available = models.BooleanField(default=True, help_text='False = explicitly unavailable / day off')
    notes = models.CharField(max_length=255, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'Availabilities'
        ordering = ['date', 'user', 'start_time']
        unique_together = ('user', 'date')

    def __str__(self):
        status = 'Available' if self.is_available else 'Unavailable'
        return f'{self.user.get_full_name()} — {self.date} ({self.get_preset_display()}: {self.start_time:%H:%M}–{self.end_time:%H:%M}) [{status}]'


# ---------------------------------------------------------------------------
# PTO (Paid Time Off) — leave requests
# ---------------------------------------------------------------------------

class PTORequest(models.Model):
    """Paid Time Off / Leave requests."""
    TYPE_CHOICES = [
        ('annual', 'Annual Leave'),
        ('sick', 'Sick Leave'),
        ('personal', 'Personal Leave'),
        ('unpaid', 'Unpaid Leave'),
        ('other', 'Other'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='pto_requests')
    leave_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.TextField(blank=True, default='')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_ptos')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True, default='', help_text='Admin/manager notes')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['start_date', 'end_date']),
        ]

    def clean(self):
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValidationError('End date must be on or after start date.')

    def __str__(self):
        return f'{self.user.get_full_name()} — {self.leave_type} ({self.start_date} to {self.end_date})'


# ---------------------------------------------------------------------------
# Drop Request — request to drop / swap an assigned shift
# ---------------------------------------------------------------------------

class DropRequest(models.Model):
    """Request to drop or swap a rostered shift."""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    shift = models.ForeignKey(RosterShift, on_delete=models.CASCADE, related_name='drop_requests')
    requested_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='drop_requests')
    reason = models.TextField(blank=True, default='')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_drops')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Drop: {self.shift} — {self.get_status_display()}'


# ---------------------------------------------------------------------------
# Notification — in-app notification log
# ---------------------------------------------------------------------------

class Notification(models.Model):
    """In-app notifications + delivery tracking for email/WhatsApp."""
    TYPE_CHOICES = [
        ('shift_assigned', 'Shift Assigned'),
        ('shift_updated', 'Shift Updated'),
        ('shift_cancelled', 'Shift Cancelled'),
        ('drop_request', 'Drop Request'),
        ('drop_approved', 'Drop Approved'),
        ('drop_rejected', 'Drop Rejected'),
        ('pto_request', 'PTO Request'),
        ('pto_approved', 'PTO Approved'),
        ('pto_rejected', 'PTO Rejected'),
        ('reminder', 'Shift Reminder'),
        ('conflict', 'Schedule Conflict'),
    ]
    CHANNEL_CHOICES = [
        ('in_app', 'In-App'),
        ('email', 'Email'),
        ('whatsapp', 'WhatsApp'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='roster_notifications')
    notification_type = models.CharField(max_length=30, choices=TYPE_CHOICES)
    channel = models.CharField(max_length=20, choices=CHANNEL_CHOICES, default='in_app')
    title = models.CharField(max_length=255)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    related_shift = models.ForeignKey(RosterShift, on_delete=models.SET_NULL, null=True, blank=True)
    sent_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-sent_at']
        indexes = [
            models.Index(fields=['user', 'is_read']),
        ]

    def __str__(self):
        return f'{self.title} → {self.user.get_full_name()}'
