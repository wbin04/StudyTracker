import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger
from django.utils import timezone
from django.conf import settings
import atexit

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler = None

def send_study_notification():
    """Check for study sessions that need notifications and send them"""
    try:
        from .models import StudySession
        
        # Get sessions that should receive notifications
        sessions_to_notify = StudySession.objects.filter(
            notification_enabled=True,
            notification_sent=False,
            status='Planned'
        )
        
        for session in sessions_to_notify:
            if session.should_send_notification():
                # Send notification using the session's built-in fields
                send_session_notification(session)
        
    except Exception as e:
        logger.error(f"Error checking for notifications: {e}")

def send_session_notification(session):
    """Send notification for a specific study session"""
    try:
        # Mark notification as sent in the StudySession itself
        session.mark_notification_sent()
        
        # Create a user-visible notification on the website
        create_user_notification(session)
        
        # If Google Calendar sync is enabled, update the main session event with notification time
        if session.sync_to_google and session.google_event_id:
            try_update_session_with_notification_time(session)
        
        logger.info(f"Notification sent for session: {session.subject} to {session.user.username}")
        
    except Exception as e:
        logger.error(f"Error sending notification for session {session.id}: {e}")

def create_user_notification(session):
    """Create a notification that appears on the website for the user"""
    try:
        from .models import Notification
        
        # Create a notification that will appear in the user's notification list
        notification, created = Notification.objects.get_or_create(
            user=session.user,
            study_session=session,
            notification_type='reminder',
            title=f"🔔 Study Reminder: {session.subject}",
            defaults={
                'message': session.get_default_notification_message(),
            }
        )
        
        if created:
            logger.info(f"Created user notification for session: {session.subject}")
        
    except Exception as e:
        logger.error(f"Error creating user notification: {e}")

def try_update_session_with_notification_time(session):
    """Update the main Google Calendar event to include notification reminder time"""
    try:
        from .models import GoogleCalendarIntegration
        from .google_calendar_service import GoogleCalendarService
        
        # Check if user has Google Calendar integration
        integration = GoogleCalendarIntegration.objects.get(user=session.user, sync_enabled=True)
        
        service = GoogleCalendarService()
        
        # Update the existing session event with the notification reminder
        success, message = service.update_calendar_event_with_notification(session.user, session)
        
        if success:
            logger.info(f"Updated Google Calendar session event with notification time for {session.user.username}")
        else:
            logger.warning(f"Failed to update Google Calendar session with notification: {message}")
            
    except GoogleCalendarIntegration.DoesNotExist:
        pass  # User doesn't have Google Calendar integration
    except Exception as e:
        logger.error(f"Error updating Google Calendar session with notification: {e}")

def start_scheduler():
    """Start the background scheduler"""
    global scheduler
    
    if scheduler is not None:
        return  # Already started
    
    try:
        scheduler = BackgroundScheduler(timezone=timezone.get_current_timezone())
        scheduler.start()
        
        # Add a job to check for notifications every minute
        scheduler.add_job(
            send_study_notification,
            'interval',
            minutes=1,
            id='check_session_notifications',
            replace_existing=True
        )
        
        logger.info("Background scheduler started successfully")
        
        # Register shutdown
        atexit.register(shutdown_scheduler)
        
    except Exception as e:
        logger.error(f"Failed to start scheduler: {e}")

def shutdown_scheduler():
    """Shutdown the background scheduler"""
    global scheduler
    
    if scheduler:
        scheduler.shutdown()
        scheduler = None
        logger.info("Background scheduler shut down")

def get_scheduler():
    """Get the global scheduler instance"""
    return scheduler