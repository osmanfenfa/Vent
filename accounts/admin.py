from django.contrib import admin
from .models import Profile

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'full_name', 'role', 'student_id', 'email_verified']
    list_filter = ['role', 'email_verified']
    search_fields = ['user__username', 'user__email', 'full_name', 'student_id']
    list_editable = ['role', 'email_verified']
