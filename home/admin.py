from django.contrib import admin
from .models import Issue, ActivityLog, UserProfile, Department, Notification


@admin.register(Issue)
class IssueAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'category', 'priority', 'status', 'department', 'assigned_to', 'created_at']
    list_filter = ['status', 'category', 'priority', 'department', 'created_at']
    search_fields = ['title', 'description', 'location']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ['id', 'issue', 'action', 'user', 'timestamp']
    list_filter = ['timestamp']
    search_fields = ['action', 'issue__title']
    date_hierarchy = 'timestamp'
    ordering = ['-timestamp']
    readonly_fields = ['timestamp']


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'phone', 'is_active']
    list_filter = ['role', 'is_active']
    search_fields = ['user__username', 'user__email', 'phone']
    ordering = ['user__username']


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'phone', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description', 'email']
    ordering = ['name']


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'title', 'notification_type', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read', 'created_at']
    search_fields = ['title', 'message', 'user__username']
    ordering = ['-created_at']
    readonly_fields = ['created_at']


# Customize admin site
admin.site.site_header = "Smart City Issue Reporting - Admin Panel"
admin.site.site_title = "Admin Panel"
admin.site.index_title = "Welcome to Administration"
