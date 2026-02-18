from django.contrib import admin
from .models import Media


@admin.register(Media)
class MediaAdmin(admin.ModelAdmin):
    list_display = ('name', 'file_type', 'mime_type', 'size', 'content_type', 'object_id', 'uploaded_by', 'created_at')
    list_filter = ('file_type', 'content_type', 'created_at')
    search_fields = ('name', 'mime_type')
    readonly_fields = ('mime_type', 'size', 'created_at')
    raw_id_fields = ('uploaded_by',)
