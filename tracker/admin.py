from django.contrib import admin
from .models import StudySession, GoogleCalendarIntegration, Notification

@admin.register(StudySession)
class StudySessionAdmin(admin.ModelAdmin):
    list_display = ('subject', 'user', 'study_date', 'start_time', 'end_time', 'status', 'sync_to_google')
    search_fields = ('subject', 'description')
    list_filter = ('status', 'study_date', 'sync_to_google')
    ordering = ['-study_date', '-start_time']

@admin.register(GoogleCalendarIntegration)
class GoogleCalendarIntegrationAdmin(admin.ModelAdmin):
    list_display = ('user', 'sync_enabled', 'created_at', 'updated_at')
    list_filter = ('sync_enabled', 'created_at')
    readonly_fields = ('google_access_token', 'google_refresh_token', 'google_token_expiry')

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'notification_type', 'is_read', 'created_at')
    list_filter = ('notification_type', 'is_read', 'created_at')
    search_fields = ('title', 'message')
