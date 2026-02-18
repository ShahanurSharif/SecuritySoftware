from django.db import models


class Address(models.Model):
    """Shared, normalised address — used by Company and Branch."""
    flat = models.CharField(max_length=50, blank=True, default='')
    street = models.CharField(max_length=255)
    suburb = models.CharField(max_length=100, blank=True, default='')
    postal_code = models.CharField(max_length=20, blank=True, default='')
    state = models.CharField(max_length=100, blank=True, default='')
    country = models.CharField(max_length=100, blank=True, default='')

    class Meta:
        verbose_name_plural = 'addresses'
        indexes = [
            models.Index(fields=['state', 'suburb']),
        ]

    def __str__(self):
        parts = filter(None, [self.flat, self.street, self.suburb, self.state, self.postal_code, self.country])
        return ', '.join(parts)


class Company(models.Model):
    name = models.CharField(max_length=255, unique=True)
    email = models.EmailField()
    description = models.TextField(blank=True, default='')
    address = models.OneToOneField(Address, on_delete=models.CASCADE, related_name='company')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'companies'
        ordering = ['name']

    def __str__(self):
        return self.name


class CompanyPhone(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='phones')
    number = models.CharField(max_length=30)
    label = models.CharField(max_length=50, blank=True, default='')

    class Meta:
        unique_together = ('company', 'number')

    def __str__(self):
        return f'{self.number} ({self.label})' if self.label else self.number
