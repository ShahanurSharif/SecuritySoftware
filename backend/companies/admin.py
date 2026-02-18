from django.contrib import admin
from .models import Address, Company, CompanyPhone


class CompanyPhoneInline(admin.TabularInline):
    model = CompanyPhone
    extra = 1


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'address')
    search_fields = ('name', 'email')
    inlines = [CompanyPhoneInline]


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ('street', 'suburb', 'state', 'postal_code', 'country')
    search_fields = ('street', 'suburb', 'state')
