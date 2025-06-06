"""
Google Calendar integration service for Study Tracker
"""
import json
from datetime import datetime, timedelta
from django.conf import settings
from django.contrib.auth.models import User
from django.utils import timezone
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from .models import GoogleCalendarIntegration, StudySession


class GoogleCalendarService:
    """Service class to handle Google Calendar operations"""
    
    def __init__(self):
        self.scopes = settings.GOOGLE_OAUTH_SCOPES
        self.client_id = settings.GOOGLE_OAUTH_CLIENT_ID
        self.client_secret = settings.GOOGLE_OAUTH_CLIENT_SECRET
        self.redirect_uri = settings.GOOGLE_CALENDAR_REDIRECT_URI
    
    def get_authorization_url(self, state=None):
        """Generate Google OAuth authorization URL"""
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [self.redirect_uri]
                }
            },
            scopes=self.scopes,
            state=state
        )
        flow.redirect_uri = self.redirect_uri
        
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'
        )
        
        return authorization_url, state
    
    def handle_oauth_callback(self, user, authorization_code, state=None):
        """Handle OAuth callback and save credentials"""
        try:
            flow = Flow.from_client_config(
                {
                    "web": {
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "redirect_uris": [self.redirect_uri]
                    }
                },
                scopes=self.scopes,
                state=state
            )
            flow.redirect_uri = self.redirect_uri
            
            # Exchange authorization code for access token
            flow.fetch_token(code=authorization_code)
            credentials = flow.credentials
            
            # Save or update user's Google Calendar integration
            integration, created = GoogleCalendarIntegration.objects.get_or_create(
                user=user,
                defaults={
                    'google_access_token': credentials.token,
                    'google_refresh_token': credentials.refresh_token,
                    'google_token_expiry': credentials.expiry,
                    'sync_enabled': True
                }
            )
            
            if not created:
                integration.google_access_token = credentials.token
                integration.google_refresh_token = credentials.refresh_token
                integration.google_token_expiry = credentials.expiry
                integration.sync_enabled = True
                integration.save()
            
            return True, "Google Calendar integrated successfully!"
            
        except Exception as e:
            return False, f"Error integrating Google Calendar: {str(e)}"
    
    def get_credentials(self, user):
        """Get valid credentials for a user"""
        try:
            integration = GoogleCalendarIntegration.objects.get(user=user)
            
            if not integration.google_access_token:
                return None
            
            credentials = Credentials(
                token=integration.google_access_token,
                refresh_token=integration.google_refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=self.client_id,
                client_secret=self.client_secret,
                scopes=self.scopes
            )
            
            # Refresh token if expired
            if credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())
                
                # Update stored credentials
                integration.google_access_token = credentials.token
                integration.google_token_expiry = credentials.expiry
                integration.save()
            
            return credentials
            
        except GoogleCalendarIntegration.DoesNotExist:
            return None
        except Exception as e:
            print(f"Error getting credentials: {e}")
            return None
    
    def create_calendar_event(self, user, study_session):
        """Create a Google Calendar event for a study session"""
        credentials = self.get_credentials(user)
        if not credentials:
            return False, "No valid Google Calendar credentials"
        
        try:
            service = build('calendar', 'v3', credentials=credentials)
            
            # Get local timezone
            local_tz = timezone.get_current_timezone()
            
            # Combine date and time for start and end with proper timezone
            start_datetime = datetime.combine(study_session.study_date, study_session.start_time)
            end_datetime = datetime.combine(study_session.study_date, study_session.end_time)
            
            # Make timezone aware using Django's timezone utilities
            start_datetime = timezone.make_aware(start_datetime, local_tz)
            end_datetime = timezone.make_aware(end_datetime, local_tz)
            
            event = {
                'summary': f'Study Session: {study_session.subject}',
                'description': f'Subject: {study_session.subject}\n'
                              f'Description: {study_session.description or "No description"}\n'
                              f'Status: {study_session.status}\n'
                              f'Notification: {study_session.reminder_minutes} minutes before\n'
                              f'Created via Study Tracker',
                'start': {
                    'dateTime': start_datetime.isoformat(),
                    'timeZone': str(local_tz),
                },
                'end': {
                    'dateTime': end_datetime.isoformat(),
                    'timeZone': str(local_tz),
                },
                'reminders': {
                    'useDefault': False,
                    'overrides': [],  # No reminders initially - will be added when notification is triggered
                },
            }
            
            # Create the event
            created_event = service.events().insert(calendarId='primary', body=event).execute()
            
            # Update study session with Google event ID
            study_session.google_event_id = created_event['id']
            study_session.last_synced = datetime.now()
            study_session.save()
            
            return True, f"Event created: {created_event.get('htmlLink')}"
            
        except HttpError as error:
            return False, f"Google Calendar API error: {error}"
        except Exception as e:
            return False, f"Error creating calendar event: {str(e)}"
    
    def update_calendar_event(self, user, study_session):
        """Update an existing Google Calendar event for a study session"""
        credentials = self.get_credentials(user)
        if not credentials:
            return False, "No valid Google Calendar credentials"
        
        if not study_session.google_event_id:
            return self.create_calendar_event(user, study_session)
        
        try:
            service = build('calendar', 'v3', credentials=credentials)
            
            # Get local timezone
            local_tz = timezone.get_current_timezone()
            
            # Combine date and time for start and end with proper timezone
            start_datetime = datetime.combine(study_session.study_date, study_session.start_time)
            end_datetime = datetime.combine(study_session.study_date, study_session.end_time)
            
            # Make timezone aware using Django's timezone utilities
            start_datetime = timezone.make_aware(start_datetime, local_tz)
            end_datetime = timezone.make_aware(end_datetime, local_tz)
            
            event = {
                'summary': f'Study Session: {study_session.subject}',
                'description': f'Subject: {study_session.subject}\n'
                              f'Description: {study_session.description or "No description"}\n'
                              f'Status: {study_session.status}\n'
                              f'Updated via Study Tracker',
                'start': {
                    'dateTime': start_datetime.isoformat(),
                    'timeZone': str(local_tz),
                },
                'end': {
                    'dateTime': end_datetime.isoformat(),
                    'timeZone': str(local_tz),
                },
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'email', 'minutes': 24 * 60},  # 1 day before
                        {'method': 'popup', 'minutes': 30},        # 30 minutes before
                    ],
                },
            }
            
            # Update the event
            updated_event = service.events().update(
                calendarId='primary', 
                eventId=study_session.google_event_id, 
                body=event
            ).execute()
            
            # Update last synced time
            study_session.last_synced = datetime.now()
            study_session.save()
            
            return True, f"Event updated: {updated_event.get('htmlLink')}"
            
        except HttpError as error:
            if error.resp.status == 404:
                # Event not found, create a new one
                return self.create_calendar_event(user, study_session)
            return False, f"Google Calendar API error: {error}"
        except Exception as e:
            return False, f"Error updating calendar event: {str(e)}"
    
    def delete_calendar_event(self, user, study_session):
        """Delete a Google Calendar event for a study session"""
        credentials = self.get_credentials(user)
        if not credentials:
            return False, "No valid Google Calendar credentials"
        
        if not study_session.google_event_id:
            return True, "No event to delete"
        
        try:
            service = build('calendar', 'v3', credentials=credentials)
            
            # Delete the event
            service.events().delete(
                calendarId='primary', 
                eventId=study_session.google_event_id
            ).execute()
            
            # Clear Google event ID
            study_session.google_event_id = None
            study_session.last_synced = None
            study_session.save()
            
            return True, "Event deleted from Google Calendar"
            
        except HttpError as error:
            if error.resp.status == 404:
                # Event already doesn't exist
                study_session.google_event_id = None
                study_session.last_synced = None
                study_session.save()
                return True, "Event was already deleted"
            return False, f"Google Calendar API error: {error}"
        except Exception as e:
            return False, f"Error deleting calendar event: {str(e)}"
    
    def sync_session(self, user, study_session):
        """Smart sync method that creates, updates, or deletes based on session state"""
        if not study_session.sync_to_google:
            # If sync is disabled but event exists, delete it
            if study_session.google_event_id:
                return self.delete_calendar_event(user, study_session)
            return True, "Sync disabled, no action needed"
        
        # If sync is enabled
        if study_session.google_event_id:
            # Update existing event
            return self.update_calendar_event(user, study_session)
        else:
            # Create new event
            return self.create_calendar_event(user, study_session)
    
    def create_generic_calendar_event(self, user, event_data):
        """Create a generic Google Calendar event with provided data"""
        credentials = self.get_credentials(user)
        if not credentials:
            return False, "No valid Google Calendar credentials", None
        
        try:
            service = build('calendar', 'v3', credentials=credentials)
            
            # Create the event
            created_event = service.events().insert(calendarId='primary', body=event_data).execute()
            
            return True, f"Event created: {created_event.get('htmlLink')}", created_event['id']
            
        except HttpError as error:
            return False, f"Google Calendar API error: {error}", None
        except Exception as e:
            return False, f"Error creating calendar event: {str(e)}", None
    
    def update_calendar_event_with_notification(self, user, study_session):
        """Update the main Google Calendar event to include notification reminder"""
        credentials = self.get_credentials(user)
        if not credentials:
            return False, "No valid Google Calendar credentials"
        
        if not study_session.google_event_id:
            return False, "No Google Calendar event found for this session"
        
        try:
            service = build('calendar', 'v3', credentials=credentials)
            
            # Get local timezone
            local_tz = timezone.get_current_timezone()
            
            # Combine date and time for start and end with proper timezone
            start_datetime = datetime.combine(study_session.study_date, study_session.start_time)
            end_datetime = datetime.combine(study_session.study_date, study_session.end_time)
            
            # Make timezone aware using Django's timezone utilities
            start_datetime = timezone.make_aware(start_datetime, local_tz)
            end_datetime = timezone.make_aware(end_datetime, local_tz)
            
            # Update the notification message in the description
            notification_status = "✅ Notification sent" if study_session.notification_sent else "⏰ Notification pending"
            notification_time = f"Reminder: {study_session.reminder_minutes} minutes before session"
            
            event = {
                'summary': f'Study Session: {study_session.subject}',
                'description': f'Subject: {study_session.subject}\n'
                              f'Description: {study_session.description or "No description"}\n'
                              f'Status: {study_session.status}\n'
                              f'{notification_status}\n'
                              f'{notification_time}\n'
                              f'Custom message: {study_session.notification_message or "Default notification"}\n'
                              f'Updated via Study Tracker',
                'start': {
                    'dateTime': start_datetime.isoformat(),
                    'timeZone': str(local_tz),
                },
                'end': {
                    'dateTime': end_datetime.isoformat(),
                    'timeZone': str(local_tz),
                },
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'email', 'minutes': study_session.reminder_minutes},  # Use the session's reminder time
                        {'method': 'popup', 'minutes': study_session.reminder_minutes},   # Use the session's reminder time
                    ],
                },
            }
            
            # Update the event
            updated_event = service.events().update(
                calendarId='primary', 
                eventId=study_session.google_event_id, 
                body=event
            ).execute()
            
            # Update last synced time
            study_session.last_synced = datetime.now()
            study_session.save()
            
            return True, f"Event updated with notification info: {updated_event.get('htmlLink')}"
            
        except HttpError as error:
            return False, f"Google Calendar API error: {error}"
        except Exception as e:
            return False, f"Error updating calendar event with notification: {str(e)}"
