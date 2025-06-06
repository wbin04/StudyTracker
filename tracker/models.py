from django.db import models
from django import forms
from datetime import datetime
from django.contrib.auth.models import User
import json

class GoogleCalendarIntegration(models.Model):
    """Model to store Google Calendar integration data for users"""
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    google_access_token = models.TextField(blank=True, null=True)
    google_refresh_token = models.TextField(blank=True, null=True)
    google_token_expiry = models.DateTimeField(blank=True, null=True)
    google_calendar_id = models.CharField(max_length=255, blank=True, null=True)
    sync_enabled = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Google Calendar for {self.user.username}"
    
    def get_credentials_dict(self):
        """Return credentials in the format expected by Google API"""
        if not self.google_access_token:
            return None
        
        return {
            'token': self.google_access_token,
            'refresh_token': self.google_refresh_token,
            'token_uri': 'https://oauth2.googleapis.com/token',
            'client_id': None,  # Will be filled from settings
            'client_secret': None,  # Will be filled from settings
            'scopes': ['https://www.googleapis.com/auth/calendar']
        }

class StudySession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    subject = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    study_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    duration = models.DurationField(blank=True, null=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ('Planned', 'Planned'),
            ('Completed', 'Completed'),
            ('Missed', 'Missed'),
        ],
        default='Planned'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Google Calendar integration fields
    google_event_id = models.CharField(max_length=255, blank=True, null=True, 
                                     help_text="Google Calendar event ID")
    sync_to_google = models.BooleanField(default=False,
                                       help_text="Whether to sync this session to Google Calendar")
    last_synced = models.DateTimeField(blank=True, null=True,
                                     help_text="Last time this session was synced to Google Calendar")
    
    # Built-in notification fields
    notification_enabled = models.BooleanField(default=True, 
                                             help_text="Enable notifications for this session")
    notification_message = models.TextField(blank=True, null=True,
                                          help_text="Custom notification message")
    notification_sent = models.BooleanField(default=False,
                                          help_text="Whether notification has been sent")
    notification_sent_at = models.DateTimeField(blank=True, null=True,
                                               help_text="When notification was sent")
    reminder_minutes = models.IntegerField(default=30,
                                         help_text="Minutes before session to send reminder")
    # Google Calendar notification sync
    google_notification_event_id = models.CharField(max_length=255, blank=True, null=True,
                                                   help_text="Google Calendar notification event ID")

    class Meta:
        ordering = ['-study_date', '-start_time']

    def __str__(self):
        return f"{self.subject} - {self.study_date} {self.start_time}"

    def save(self, *args, **kwargs):
        if self.start_time and self.end_time:
            start_datetime = datetime.combine(datetime.today(), self.start_time)
            end_datetime = datetime.combine(datetime.today(), self.end_time)
            self.duration = end_datetime - start_datetime
        super().save(*args, **kwargs)
    
    def get_default_notification_message(self):
        """Get the default notification message for this session"""
        if self.notification_message:
            return self.notification_message
        return f"Your study session '{self.subject}' is starting in {self.reminder_minutes} minutes at {self.start_time.strftime('%H:%M')}."
    
    def should_send_notification(self):
        """Check if notification should be sent for this session"""
        from django.utils import timezone
        from datetime import datetime, timedelta
        
        if not self.notification_enabled or self.notification_sent or self.status != 'Planned':
            return False
        
        # Calculate notification time
        session_datetime = datetime.combine(self.study_date, self.start_time)
        session_datetime = timezone.make_aware(session_datetime)
        notification_time = session_datetime - timedelta(minutes=self.reminder_minutes)
        
        # Check if it's time to send notification (with a 2-minute window for better accuracy)
        now = timezone.now()
        time_window = timedelta(minutes=2)
        
        # Send notification if we're within the time window and before the session starts
        return (notification_time - time_window <= now <= session_datetime)
    
    def mark_notification_sent(self):
        """Mark notification as sent"""
        from django.utils import timezone
        self.notification_sent = True
        self.notification_sent_at = timezone.now()
        self.save(update_fields=['notification_sent', 'notification_sent_at'])

class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    study_session = models.ForeignKey(StudySession, on_delete=models.CASCADE, blank=True, null=True)
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(
        max_length=20,
        choices=[
            ('reminder', 'Reminder'),
            ('achievement', 'Achievement'),
            ('system', 'System'),
        ],
        default='reminder'
    )
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        # Add unique constraint to prevent duplicate notifications
        unique_together = [['user', 'study_session', 'notification_type', 'title']]
    
    def __str__(self):
        return f"{self.title} - {self.user.username}"
