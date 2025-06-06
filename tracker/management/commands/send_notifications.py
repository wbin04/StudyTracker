from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, timedelta
from tracker.models import StudySession, Notification
from tracker.views import create_system_notification


class Command(BaseCommand):
    help = 'Send automated notifications for study sessions'

    def add_arguments(self, parser):
        parser.add_argument(
            '--type',
            type=str,
            choices=['daily', 'hourly', 'immediate'],
            default='hourly',
            help='Type of notification check to run'
        )

    def handle(self, *args, **options):
        notification_type = options['type']
        
        if notification_type == 'daily':
            self.send_daily_reminders()
        elif notification_type == 'hourly':
            self.send_hourly_reminders()
        elif notification_type == 'immediate':
            self.send_immediate_reminders()
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully processed {notification_type} notifications')
        )

    def send_daily_reminders(self):
        """Send daily reminders for sessions happening tomorrow"""
        tomorrow = timezone.now().date() + timedelta(days=1)
        
        # Get sessions happening tomorrow
        upcoming_sessions = StudySession.objects.filter(
            study_date=tomorrow,
            status='Planned'
        ).select_related('user')
        
        count = 0
        for session in upcoming_sessions:
            # Check if daily reminder already exists
            existing_reminder = Notification.objects.filter(
                user=session.user,
                study_session=session,
                notification_type='reminder',
                title__contains="Tomorrow's Study Session",
                created_at__date=timezone.now().date()
            ).exists()
            
            if not existing_reminder:
                create_system_notification(
                    user=session.user,
                    title="Tomorrow's Study Session",
                    message=f"Don't forget about your {session.subject} session tomorrow at {session.start_time.strftime('%H:%M')}! Make sure you're prepared.",
                    session=session
                )
                count += 1
        
        self.stdout.write(f'Sent {count} daily reminders')

    def send_hourly_reminders(self):
        """Send reminders for sessions starting within the next hour"""
        now = timezone.now()
        one_hour_later = now + timedelta(hours=1)
        
        # Get sessions starting within the next hour
        upcoming_sessions = StudySession.objects.filter(
            study_date=now.date(),
            start_time__gte=now.time(),
            start_time__lt=one_hour_later.time(),
            status='Planned'
        ).select_related('user')
        
        count = 0
        for session in upcoming_sessions:
            session_datetime = datetime.combine(session.study_date, session.start_time)
            minutes_until = int((session_datetime - now.replace(tzinfo=None)).total_seconds() / 60)
            
            # Only send if session is starting in 30-60 minutes and no recent reminder exists
            if 30 <= minutes_until <= 60:
                recent_reminder = Notification.objects.filter(
                    user=session.user,
                    study_session=session,
                    notification_type='reminder',
                    created_at__gte=now - timedelta(hours=2)
                ).exists()
                
                if not recent_reminder:
                    create_system_notification(
                        user=session.user,
                        title=f"Study Session Starting Soon: {session.subject}",
                        message=f"Your {session.subject} session is starting in {minutes_until} minutes. Get ready!",
                        session=session
                    )
                    count += 1
        
        self.stdout.write(f'Sent {count} hourly reminders')

    def send_immediate_reminders(self):
        """Send immediate reminders for sessions starting in 15 minutes"""
        now = timezone.now()
        fifteen_minutes_later = now + timedelta(minutes=15)
        
        # Get sessions starting in approximately 15 minutes
        upcoming_sessions = StudySession.objects.filter(
            study_date=now.date(),
            start_time__gte=now.time(),
            start_time__lt=fifteen_minutes_later.time(),
            status='Planned'
        ).select_related('user')
        
        count = 0
        for session in upcoming_sessions:
            session_datetime = datetime.combine(session.study_date, session.start_time)
            minutes_until = int((session_datetime - now.replace(tzinfo=None)).total_seconds() / 60)
            
            # Send immediate reminder for sessions starting in 10-20 minutes
            if 10 <= minutes_until <= 20:
                recent_immediate = Notification.objects.filter(
                    user=session.user,
                    study_session=session,
                    notification_type='reminder',
                    title__contains="Starting Now",
                    created_at__gte=now - timedelta(minutes=30)
                ).exists()
                
                if not recent_immediate:
                    create_system_notification(
                        user=session.user,
                        title=f"Study Session Starting Now: {session.subject}",
                        message=f"⏰ Your {session.subject} session is starting in {minutes_until} minutes! Time to begin!",
                        session=session
                    )
                    count += 1
        
        self.stdout.write(f'Sent {count} immediate reminders')