from django.contrib import admin
from .models import Profile, ProfileAddress


@admin.register(ProfileAddress)
class ProfileAddressAdmin(admin.ModelAdmin):
    list_display = ('flat', 'street', 'suburb', 'state', 'postal_code', 'country')
    search_fields = ('street', 'suburb', 'state', 'country')


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'group', 'status', 'phone')
    list_filter = ('role', 'group', 'status')
    search_fields = ('user__first_name', 'user__last_name', 'user__email', 'phone')
    raw_id_fields = ('user', 'address', 'photo')
