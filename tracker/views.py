from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import StudySession, GoogleCalendarIntegration, Notification
from .forms import StudySessionForm, UserRegistrationForm
from .google_calendar_service import GoogleCalendarService
import secrets
from datetime import datetime, timedelta

# ===== HELPER FUNCTIONS =====

def create_system_notification(user, title, message, session=None):
    """Helper function to create system notifications - kept only for Google Calendar sync messages"""
    from .models import Notification
    notification, created = Notification.objects.get_or_create(
        user=user,
        study_session=session,
        notification_type='system',
        title=title,
        defaults={
            'message': message,
        }
    )
    return notification

def create_achievement_notification(user, title, message, session=None):
    """Helper function to create achievement notifications"""
    from .models import Notification
    notification, created = Notification.objects.get_or_create(
        user=user,
        study_session=session,
        notification_type='achievement',
        title=title,
        defaults={
            'message': message,
        }
    )
    return notification

# ===== VIEW FUNCTIONS =====

def home(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'tracker/index.html')

@login_required
def dashboard(request):
    return render(request, 'tracker/dashboard.html')

@login_required
def session_list(request):
    sessions = StudySession.objects.filter(user=request.user)
    return render(request, 'tracker/session_list.html', {'sessions': sessions})

@login_required
def session_create(request):
    if request.method == 'POST':
        form = StudySessionForm(request.POST)
        if form.is_valid():
            session = form.save(commit=False)
            session.user = request.user
            session.save()
            
            messages.success(request, 'Study session created successfully!')
            
            # Auto sync to Google Calendar if enabled
            if session.sync_to_google:
                try:
                    integration = GoogleCalendarIntegration.objects.get(user=request.user, sync_enabled=True)
                    service = GoogleCalendarService()
                    success, message = service.sync_session(request.user, session)
                    
                    if success:
                        create_system_notification(
                            user=request.user,
                            title="Google Calendar Sync",
                            message=f"Your study session '{session.subject}' has been successfully synced to Google Calendar.",
                            session=session
                        )
                    else:
                        messages.warning(request, f'Sync to Google Calendar failed: {message}')
                except GoogleCalendarIntegration.DoesNotExist:
                    messages.warning(request, 'Google Calendar is not connected.')
                
            return redirect('session_list')
    else:
        form = StudySessionForm()
    return render(request, 'tracker/session_form.html', {'form': form})

@login_required
def session_edit(request, pk):
    session = get_object_or_404(StudySession, pk=pk, user=request.user)
    old_sync_status = session.sync_to_google
    old_date = session.study_date
    old_time = session.start_time
    
    if request.method == 'POST':
        form = StudySessionForm(request.POST, instance=session)
        if form.is_valid():
            updated_session = form.save()
            
            # Check if session time/date was changed
            if old_date != updated_session.study_date or old_time != updated_session.start_time:
                create_system_notification(
                    user=request.user,
                    title="Study Session Updated",
                    message=f"Your study session '{updated_session.subject}' has been rescheduled to {updated_session.study_date.strftime('%B %d, %Y')} at {updated_session.start_time.strftime('%H:%M')}.",
                    session=updated_session
                )
            
            # Check if sync status changed or session details changed
            if updated_session.sync_to_google != old_sync_status or updated_session.sync_to_google:
                try:
                    integration = GoogleCalendarIntegration.objects.get(user=request.user, sync_enabled=True)
                    service = GoogleCalendarService()
                    success, message = service.sync_session(request.user, updated_session)
                    
                    if success:
                        messages.success(request, 'Study session updated and synced to Google Calendar!')
                    else:
                        messages.warning(request, f'Study session updated but sync failed: {message}')
                except GoogleCalendarIntegration.DoesNotExist:
                    messages.warning(request, 'Study session updated but Google Calendar is not connected.')
            else:
                messages.success(request, 'Study session updated successfully!')
                
            return redirect('session_list')
    else:
        form = StudySessionForm(instance=session)
    return render(request, 'tracker/session_form.html', {'form': form, 'session': session})

@login_required
def session_delete(request, pk):
    session = get_object_or_404(StudySession, pk=pk, user=request.user)
    if request.method == 'POST':
        # If session is synced to Google Calendar, try to delete it there too
        if session.sync_to_google and session.google_event_id:
            try:
                integration = GoogleCalendarIntegration.objects.get(user=request.user, sync_enabled=True)
                service = GoogleCalendarService()
                success, message = service.delete_calendar_event(request.user, session)
                
                if not success:
                    messages.warning(request, f'Session deleted locally but failed to delete from Google Calendar: {message}')
            except GoogleCalendarIntegration.DoesNotExist:
                pass  # Just delete locally
        
        session.delete()
        messages.success(request, 'Study session deleted successfully!')
        return redirect('session_list')
    return render(request, 'tracker/session_confirm_delete.html', {'session': session})

@login_required
def calendar_view(request):
    return render(request, 'tracker/calendar.html')

def user_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, 'tracker/login.html')

def user_logout(request):
    logout(request)
    return redirect('login')

def user_register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'Registration successful! Please login.')
            return redirect('login')
    else:
        form = UserRegistrationForm()
    return render(request, 'tracker/register.html', {'form': form})

@login_required
def google_calendar_settings(request):
    try:
        integration = GoogleCalendarIntegration.objects.get(user=request.user)
    except GoogleCalendarIntegration.DoesNotExist:
        integration = None
    
    context = {
        'integration': integration,
        'is_connected': integration and integration.sync_enabled if integration else False
    }
    return render(request, 'tracker/google_calendar_settings.html', context)

@login_required
def google_calendar_connect(request):
    service = GoogleCalendarService()
    state = secrets.token_urlsafe(32)
    request.session['google_oauth_state'] = state
    authorization_url, _ = service.get_authorization_url(state=state)
    return redirect(authorization_url)

@login_required
def google_calendar_callback(request):
    code = request.GET.get('code')
    state = request.GET.get('state')
    stored_state = request.session.get('google_oauth_state')
    
    if not code:
        messages.error(request, 'Authorization failed. No authorization code received.')
        return redirect('google_calendar_settings')
    
    if state != stored_state:
        messages.error(request, 'Authorization failed. Invalid state parameter.')
        return redirect('google_calendar_settings')
    
    service = GoogleCalendarService()
    success, message = service.handle_oauth_callback(request.user, code, state)
    
    if success:
        messages.success(request, message)
    else:
        messages.error(request, message)
    
    return redirect('google_calendar_settings')

@login_required
def google_calendar_disconnect(request):
    try:
        integration = GoogleCalendarIntegration.objects.get(user=request.user)
        integration.delete()
        messages.success(request, 'Google Calendar disconnected successfully!')
    except GoogleCalendarIntegration.DoesNotExist:
        messages.warning(request, 'No Google Calendar integration found.')
    return redirect('google_calendar_settings')

@login_required
def google_calendar_sync_all(request):
    try:
        # Check if user has Google Calendar integration
        integration = GoogleCalendarIntegration.objects.get(user=request.user, sync_enabled=True)
        
        # Get all sessions with sync enabled that haven't been synced yet or need re-sync
        sessions_to_sync = StudySession.objects.filter(
            user=request.user, 
            sync_to_google=True
        )
        
        if not sessions_to_sync.exists():
            messages.info(request, 'No sessions found with Google Calendar sync enabled.')
            return redirect('google_calendar_settings')
        service = GoogleCalendarService()
        success_count = 0
        error_count = 0
        
        for session in sessions_to_sync:
            success, message = service.sync_session(request.user, session)
            if success:
                success_count += 1
            else:
                error_count += 1
                print(f"Sync error for session {session.id}: {message}")  # Log error
        
        if success_count > 0 and error_count == 0:
            messages.success(request, f'Successfully synced {success_count} session(s) to Google Calendar!')
        elif success_count > 0 and error_count > 0:
            messages.warning(request, f'Synced {success_count} session(s) successfully, but {error_count} failed.')
        else:
            messages.error(request, f'Failed to sync {error_count} session(s) to Google Calendar.')
            
    except GoogleCalendarIntegration.DoesNotExist:
        messages.error(request, 'Google Calendar is not connected. Please connect first.')
    except Exception as e:
        messages.error(request, f'Sync failed with error: {str(e)}')
    
    return redirect('google_calendar_settings')

@login_required
def toggle_session_sync(request, session_id):
    session = get_object_or_404(StudySession, id=session_id, user=request.user)
    session.sync_to_google = not session.sync_to_google
    session.save()
      # If sync was just enabled, try to sync to Google Calendar immediately
    if session.sync_to_google:
        try:
            integration = GoogleCalendarIntegration.objects.get(user=request.user, sync_enabled=True)
            service = GoogleCalendarService()
            success, message = service.sync_session(request.user, session)
            
            status = "enabled and synced" if success else f"enabled but sync failed: {message}"
        except GoogleCalendarIntegration.DoesNotExist:
            status = "enabled but Google Calendar not connected"
    else:
        status = "disabled"
    
    return JsonResponse({'success': True, 'status': status})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_overview(request):
    sessions_count = StudySession.objects.filter(user=request.user).count()
    completed_count = StudySession.objects.filter(user=request.user, status='Completed').count()
    
    return Response({
        'total_sessions': sessions_count,
        'completed_sessions': completed_count,
        'user': request.user.username
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_calendar_events(request):
    sessions = StudySession.objects.filter(user=request.user)
    events = []
    
    for session in sessions:
        events.append({
            'id': session.id,
            'title': f'{session.subject}',
            'start': f'{session.study_date}T{session.start_time}',
            'end': f'{session.study_date}T{session.end_time}',
            'description': session.description,
            'status': session.status
        })
    
    return Response(events)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_calendar(request):
    sessions = StudySession.objects.filter(user=request.user)
    data = []
    
    for session in sessions:
        data.append({
            'id': session.id,
            'subject': session.subject,
            'date': session.study_date.strftime('%Y-%m-%d'),
            'start_time': session.start_time.strftime('%H:%M'),
            'end_time': session.end_time.strftime('%H:%M'),
            'status': session.status
        })
    
    return Response(data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_study_summary(request):
    total_sessions = StudySession.objects.filter(user=request.user).count()
    completed_sessions = StudySession.objects.filter(user=request.user, status='Completed').count()
    planned_sessions = StudySession.objects.filter(user=request.user, status='Planned').count()
    missed_sessions = StudySession.objects.filter(user=request.user, status='Missed').count()
    
    return Response({
        'total': total_sessions,
        'completed': completed_sessions,
        'planned': planned_sessions,
        'missed': missed_sessions
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_session_durations(request):
    sessions = StudySession.objects.filter(user=request.user).order_by('-study_date')[:10]  # Last 10 sessions
    data = []
    
    for session in sessions:
        if session.duration:
            # Convert duration to minutes
            duration_minutes = session.duration.total_seconds() / 60
        else:
            # Calculate duration from start and end time
            from datetime import datetime, timedelta
            start_datetime = datetime.combine(session.study_date, session.start_time)
            end_datetime = datetime.combine(session.study_date, session.end_time)
            duration = end_datetime - start_datetime
            duration_minutes = duration.total_seconds() / 60
        
        data.append({
            'subject': session.subject,
            'date': session.study_date.strftime('%m/%d'),
            'duration': round(duration_minutes, 2),
            'status': session.status
        })
    
    return Response(data)

# ===== NOTIFICATION VIEWS =====

@login_required
def notification_list(request):
    """Display paginated list of user's notifications"""
    notifications = Notification.objects.filter(user=request.user)
    
    # Filter by read/unread status
    filter_type = request.GET.get('filter', 'all')
    if filter_type == 'unread':
        notifications = notifications.filter(is_read=False)
    elif filter_type == 'read':
        notifications = notifications.filter(is_read=True)
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        notifications = notifications.filter(
            Q(title__icontains=search_query) | Q(message__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(notifications, 10)  # Show 10 notifications per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Count unread notifications
    unread_count = Notification.objects.filter(user=request.user, is_read=False).count()
    
    context = {
        'page_obj': page_obj,
        'filter_type': filter_type,
        'search_query': search_query,
        'unread_count': unread_count,
    }
    return render(request, 'tracker/notification_list.html', context)

@login_required
def notification_detail(request, pk):
    """Display notification details and mark as read"""
    notification = get_object_or_404(Notification, pk=pk, user=request.user)
    
    # Mark as read if not already read
    if not notification.is_read:
        notification.is_read = True
        notification.save()
    
    return render(request, 'tracker/notification_detail.html', {'notification': notification})

@login_required
def notification_mark_read(request, pk):
    """Mark a single notification as read"""
    notification = get_object_or_404(Notification, pk=pk, user=request.user)
    notification.is_read = True
    notification.save()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'message': 'Notification marked as read'})
    
    messages.success(request, 'Notification marked as read.')
    return redirect('notification_list')

@login_required
def notification_mark_all_read(request):
    """Mark all user's notifications as read"""
    updated_count = Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True, 
            'message': f'{updated_count} notifications marked as read',
            'count': updated_count
        })
    
    messages.success(request, f'{updated_count} notifications marked as read.')
    return redirect('notification_list')

@login_required
def notification_delete(request, pk):
    """Delete a notification"""
    notification = get_object_or_404(Notification, pk=pk, user=request.user)
    
    if request.method == 'POST':
        notification.delete()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': 'Notification deleted'})
        
        messages.success(request, 'Notification deleted successfully.')
        return redirect('notification_list')
    
    return render(request, 'tracker/notification_confirm_delete.html', {'notification': notification})

@login_required
def create_session_reminder(request, session_id):
    """Create a reminder notification for a study session"""
    session = get_object_or_404(StudySession, id=session_id, user=request.user)
    
    if request.method == 'POST':
        reminder_minutes = int(request.POST.get('reminder_minutes', 30))
        
        # Calculate reminder time - make it timezone-aware
        session_datetime = datetime.combine(session.study_date, session.start_time)
        # Make session_datetime timezone-aware
        session_datetime = timezone.make_aware(session_datetime)
        reminder_time = session_datetime - timedelta(minutes=reminder_minutes)
        
        # Check if reminder time is in the future
        if reminder_time <= timezone.now():
            messages.error(request, 'Cannot create reminder for past sessions.')
            return redirect('session_list')
        
        # Create notification
        notification = Notification.objects.create(
            user=request.user,
            study_session=session,
            title=f"Study Reminder: {session.subject}",
            message=f"Your study session '{session.subject}' is starting in {reminder_minutes} minutes at {session.start_time.strftime('%H:%M')}.",
            notification_type='reminder'
        )
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True, 
                'message': f'Reminder set for {reminder_minutes} minutes before the session',
                'notification_id': notification.id
            })
        
        messages.success(request, f'Reminder set for {reminder_minutes} minutes before the session.')
        return redirect('session_list')
    
    return render(request, 'tracker/create_reminder.html', {'session': session})

# ===== NOTIFICATION API ENDPOINTS =====

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_notifications(request):
    """Get user's notifications with pagination and filtering"""
    notifications = Notification.objects.filter(user=request.user)
    
    # Filter by type
    notification_type = request.GET.get('type')
    if notification_type:
        notifications = notifications.filter(notification_type=notification_type)
    
    # Filter by read status
    is_read = request.GET.get('is_read')
    if is_read is not None:
        notifications = notifications.filter(is_read=is_read.lower() == 'true')
    
    # Limit results
    limit = int(request.GET.get('limit', 20))
    notifications = notifications[:limit]
    
    data = []
    for notification in notifications:
        data.append({
            'id': notification.id,
            'title': notification.title,
            'message': notification.message,
            'notification_type': notification.notification_type,
            'is_read': notification.is_read,
            'created_at': notification.created_at.isoformat(),
            'study_session': {
                'id': notification.study_session.id,
                'subject': notification.study_session.subject,
                'study_date': notification.study_session.study_date.isoformat(),
            } if notification.study_session else None
        })
    
    return Response(data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_notification_counts(request):
    """Get notification counts by type and status"""
    total_count = Notification.objects.filter(user=request.user).count()
    unread_count = Notification.objects.filter(user=request.user, is_read=False).count()
    
    counts_by_type = {}
    for choice in Notification._meta.get_field('notification_type').choices:
        type_key = choice[0]
        counts_by_type[type_key] = Notification.objects.filter(
            user=request.user, 
            notification_type=type_key
        ).count()
    
    return Response({
        'total': total_count,
        'unread': unread_count,
        'by_type': counts_by_type
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_mark_notification_read(request, pk):
    """Mark a notification as read via API"""
    try:
        notification = Notification.objects.get(pk=pk, user=request.user)
        notification.is_read = True
        notification.save()
        
        return Response({
            'success': True,
            'message': 'Notification marked as read'
        })
    except Notification.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Notification not found'
        }, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_mark_all_notifications_read(request):
    """Mark all user's notifications as read via API"""
    updated_count = Notification.objects.filter(
        user=request.user, 
        is_read=False
    ).update(is_read=True)
    
    return Response({
        'success': True,
        'message': f'{updated_count} notifications marked as read',
        'count': updated_count
    })

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def api_delete_notification(request, pk):
    """Delete a notification via API"""
    try:
        notification = Notification.objects.get(pk=pk, user=request.user)
        notification.delete()
        
        return Response({
            'success': True,
            'message': 'Notification deleted'
        })
    except Notification.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Notification not found'
        }, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_create_session_reminder(request):
    """Create a reminder notification for a study session via API"""
    session_id = request.data.get('session_id')
    reminder_minutes = int(request.data.get('reminder_minutes', 30))
    
    try:
        session = StudySession.objects.get(id=session_id, user=request.user)
        
        # Calculate reminder time - make it timezone-aware
        session_datetime = datetime.combine(session.study_date, session.start_time)
        # Make session_datetime timezone-aware
        session_datetime = timezone.make_aware(session_datetime)
        reminder_time = session_datetime - timedelta(minutes=reminder_minutes)
        
        # Check if reminder time is in the future
        if reminder_time <= timezone.now():
            return Response({
                'success': False,
                'message': 'Cannot create reminder for past sessions'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create notification
        notification = Notification.objects.create(
            user=request.user,
            study_session=session,
            title=f"Study Reminder: {session.subject}",
            message=f"Your study session '{session.subject}' is starting in {reminder_minutes} minutes at {session.start_time.strftime('%H:%M')}.",
            notification_type='reminder'
        )
        
        return Response({
            'success': True,
            'message': f'Reminder set for {reminder_minutes} minutes before the session',
            'notification': {
                'id': notification.id,
                'title': notification.title,
                'message': notification.message,
                'created_at': notification.created_at.isoformat()
            }
        })
        
    except StudySession.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Study session not found'
        }, status=status.HTTP_404_NOT_FOUND)

# ===== AUTOMATIC NOTIFICATION MANAGEMENT =====

def check_and_create_session_achievements(user, session):
    """Check for achievements and create notifications"""
    completed_sessions = StudySession.objects.filter(user=user, status='Completed').count()
    
    # Achievement milestones
    milestones = [1, 5, 10, 25, 50, 100]
    
    if completed_sessions in milestones:
        create_achievement_notification(
            user=user,
            title=f"Achievement Unlocked: {completed_sessions} Sessions Completed!",
            message=f"Congratulations! You've completed {completed_sessions} study session{'s' if completed_sessions > 1 else ''}. Keep up the great work!",
            session=session
        )

def create_daily_study_reminder():
    """Create daily reminders for users with upcoming sessions"""
    from django.utils import timezone
    
    tomorrow = timezone.now().date() + timedelta(days=1)
    upcoming_sessions = StudySession.objects.filter(
        study_date=tomorrow,
        status='Planned'
    ).select_related('user')
    
    for session in upcoming_sessions:
        # Use get_or_create to prevent duplicate daily reminders
        notification, created = Notification.objects.get_or_create(
            user=session.user,
            study_session=session,
            notification_type='reminder',
            title="Tomorrow's Study Session",
            defaults={
                'message': f"Don't forget about your {session.subject} session tomorrow at {session.start_time.strftime('%H:%M')}!",
            }
        )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_mark_session_completed(request, session_id):
    """Mark a session as completed and check for achievements"""
    try:
        session = StudySession.objects.get(id=session_id, user=request.user)
        session.status = 'Completed'
        session.save()
        
        # Check for achievements
        check_and_create_session_achievements(request.user, session)
        
        return Response({
            'success': True,
            'message': 'Session marked as completed'
        })
    except StudySession.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Session not found'
        }, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_upcoming_sessions(request):
    """Get upcoming sessions for notification purposes"""
    from django.utils import timezone
    
    now = timezone.now()
    upcoming_sessions = StudySession.objects.filter(
        user=request.user,
        study_date__gte=now.date(),
        status='Planned'
    ).order_by('study_date', 'start_time')[:5]
    
    data = []
    for session in upcoming_sessions:
        session_datetime = datetime.combine(session.study_date, session.start_time)
        time_until = session_datetime - now.replace(tzinfo=None)
        
        data.append({
            'id': session.id,
            'subject': session.subject,
            'date': session.study_date.strftime('%Y-%m-%d'),
            'time': session.start_time.strftime('%H:%M'),
            'hours_until': int(time_until.total_seconds() / 3600),
            'can_create_reminder': time_until.total_seconds() > 900  # Can create reminder if more than 15 minutes away
        })
    
    return Response(data)
