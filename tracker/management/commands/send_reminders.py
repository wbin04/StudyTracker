from django.core.management.base import BaseCommand
from django.utils import timezone
from tracker.models import ScheduledReminder, Notification
from datetime import timedelta

class Command(BaseCommand):
    help = 'Send scheduled study reminders that are due'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what reminders would be sent without actually sending them',
        )

    def handle(self, *args, **options):
        now = timezone.now()
        dry_run = options.get('dry_run', False)
        
        # Find all unsent reminders that are due (reminder_time <= now)
        due_reminders = ScheduledReminder.objects.filter(
            is_sent=False,
            reminder_time__lte=now
        ).select_related('user', 'study_session')
        
        if not due_reminders.exists():
            self.stdout.write(
                self.style.SUCCESS('No reminders are due at this time.')
            )
            return
        
        sent_count = 0
        
        for reminder in due_reminders:
            # Check if the study session is still valid (not completed/cancelled)
            if reminder.study_session.status != 'Planned':
                if dry_run:
                    self.stdout.write(
                        f"Would skip: {reminder} (session status: {reminder.study_session.status})"
                    )
                else:
                    # Mark as sent to avoid future processing
                    reminder.is_sent = True
                    reminder.sent_at = now
                    reminder.save()
                continue
            
            # Check if session is in the past
            session_datetime = timezone.make_aware(
                timezone.datetime.combine(
                    reminder.study_session.study_date,
                    reminder.study_session.start_time
                )
            )
            
            if session_datetime < now:
                if dry_run:
                    self.stdout.write(
                        f"Would skip: {reminder} (session is in the past)"
                    )
                else:
                    # Mark as sent to avoid future processing
                    reminder.is_sent = True
                    reminder.sent_at = now
                    reminder.save()
                continue
            
            if dry_run:
                self.stdout.write(
                    f"Would send: {reminder.title} to {reminder.user.username}"
                )
            else:
                # Create the actual notification
                Notification.objects.create(
                    user=reminder.user,
                    study_session=reminder.study_session,
                    title=reminder.title,
                    message=reminder.message,
                    notification_type='reminder'
                )
                
                # Mark reminder as sent
                reminder.is_sent = True
                reminder.sent_at = now
                reminder.save()
                
                self.stdout.write(
                    f"Sent reminder: {reminder.title} to {reminder.user.username}"
                )
            
            sent_count += 1
        
        if dry_run:
            self.stdout.write(
                self.style.SUCCESS(f'Would send {sent_count} reminders.')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f'Successfully sent {sent_count} reminders.')
            )