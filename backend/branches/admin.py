from django.contrib import admin
from .models import Branch, BranchStaff


class BranchStaffInline(admin.TabularInline):
    model = BranchStaff
    extra = 1


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ('name', 'company', 'front_desk_number', 'store_number')
    list_filter = ('company',)
    search_fields = ('name', 'company__name')
    inlines = [BranchStaffInline]
