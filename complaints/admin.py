from django.contrib import admin
from .models import Complaint

@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'type', 'category', 'status', 'assigned_to', 'student', 'created_at']
    list_filter = ['type', 'category', 'status', 'created_at']
    search_fields = ['title', 'description', 'student__username', 'student__email']
    readonly_fields = ['created_at', 'updated_at']
    list_editable = ['status', 'assigned_to']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'type', 'category')
        }),
        ('Status & Assignment', {
            'fields': ('status', 'assigned_to')
        }),
        ('Student Information', {
            'fields': ('student',),
            'classes': ('collapse',)
        }),
        ('Attachment', {
            'fields': ('attachment',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
