from django.db import models
from companies.models import Company, Address


class Branch(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='branches')
    name = models.CharField(max_length=255)
    address = models.OneToOneField(Address, on_delete=models.CASCADE, related_name='branch')
    front_desk_number = models.CharField(max_length=30)
    store_number = models.CharField(max_length=30)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'branches'
        unique_together = ('company', 'name')
        ordering = ['company__name', 'name']
        indexes = [
            models.Index(fields=['company', 'name']),
        ]

    def __str__(self):
        return f'{self.name} ({self.company.name})'


class BranchStaff(models.Model):
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='staff')
    name = models.CharField(max_length=150)
    designation = models.CharField(max_length=100)
    phone = models.CharField(max_length=30)
    email = models.EmailField(blank=True, default='')

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f'{self.name} — {self.designation}'
