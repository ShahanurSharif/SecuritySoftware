from django.db import models
from django.contrib.auth.models import User
from media_library.models import Media


class ProfileAddress(models.Model):
    flat = models.CharField(max_length=50, blank=True, default='')
    street = models.CharField(max_length=255, blank=True, default='')
    suburb = models.CharField(max_length=100, blank=True, default='')
    postal_code = models.CharField(max_length=20, blank=True, default='')
    state = models.CharField(max_length=100, blank=True, default='')
    country = models.CharField(max_length=100, blank=True, default='')

    class Meta:
        verbose_name = 'Profile Address'
        verbose_name_plural = 'Profile Addresses'
        indexes = [
            models.Index(fields=['state', 'suburb']),
        ]

    def __str__(self):
        parts = [self.flat, self.street, self.suburb, self.state, self.postal_code, self.country]
        return ', '.join(p for p in parts if p)


class Profile(models.Model):
    ROLE_CHOICES = [
        ('Admin', 'Admin'),
        ('LPO', 'LPO'),
    ]
    GROUP_CHOICES = [
        ('Admin', 'Admin'),
        ('Manager', 'Manager'),
        ('Analyst', 'Analyst'),
        ('LPO', 'LPO'),
        ('Viewer', 'Viewer'),
    ]
    STATUS_CHOICES = [
        ('Active', 'Active'),
        ('Inactive', 'Inactive'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone = models.CharField(max_length=30, blank=True, default='')
    birthday = models.DateField(null=True, blank=True)
    photo = models.ForeignKey(Media, on_delete=models.SET_NULL, null=True, blank=True, related_name='profile_photos')
    address = models.OneToOneField(ProfileAddress, on_delete=models.SET_NULL, null=True, blank=True, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='LPO')
    group = models.CharField(max_length=20, choices=GROUP_CHOICES, default='Viewer')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Active')

    class Meta:
        ordering = ['user__first_name', 'user__last_name']

    def __str__(self):
        return f'{self.user.get_full_name()} ({self.role})'
