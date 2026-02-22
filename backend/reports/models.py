from django.db import models
from django.contrib.auth.models import User


class IncidentReport(models.Model):
    """Incident report capturing loss, recovery, damage and intervention details."""

    # ── Who / Where ──────────────────────────────────────────────
    reported_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name='incident_reports',
    )
    branch = models.ForeignKey(
        'branches.Branch', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='incident_reports',
    )

    # ── When ─────────────────────────────────────────────────────
    incident_date = models.DateField()
    incident_time = models.TimeField()

    # ── Financial ────────────────────────────────────────────────
    amount_lost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    amount_recovered = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # ── Damage ───────────────────────────────────────────────────
    damaged_items = models.CharField(max_length=500, blank=True, default='')
    description = models.TextField(blank=True, default='')

    # ── Intervention ─────────────────────────────────────────────
    police_intervention = models.BooleanField(default=False)
    injured = models.BooleanField(default=False)

    # ── Meta ─────────────────────────────────────────────────────
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-incident_date', '-incident_time']

    def __str__(self):
        branch_name = self.branch.name if self.branch else 'N/A'
        return f'Incident #{self.pk} — {branch_name} — {self.incident_date}'

    @property
    def net_loss(self):
        return self.amount_lost - self.amount_recovered
