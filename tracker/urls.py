from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('sessions/', views.session_list, name='session_list'),
    path('sessions/create/', views.session_create, name='session_create'),
    path('sessions/<int:pk>/edit/', views.session_edit, name='session_edit'),
    path('sessions/<int:pk>/delete/', views.session_delete, name='session_delete'),
    path('calendar/', views.calendar_view, name='calendar'),
    
    # Authentication URLs
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('register/', views.user_register, name='register'),
    
    # Google Calendar integration URLs
    path('google-calendar/settings/', views.google_calendar_settings, name='google_calendar_settings'),
    path('google-calendar/connect/', views.google_calendar_connect, name='google_calendar_connect'),
    path('google-calendar/callback/', views.google_calendar_callback, name='google_calendar_callback'),
    path('google-calendar/disconnect/', views.google_calendar_disconnect, name='google_calendar_disconnect'),
    path('google-calendar/sync-all/', views.google_calendar_sync_all, name='google_calendar_sync_all'),
    path('sessions/<int:session_id>/toggle-sync/', views.toggle_session_sync, name='toggle_session_sync'),
    
    # Notification URLs
    path('notifications/', views.notification_list, name='notification_list'),
    path('notifications/<int:pk>/', views.notification_detail, name='notification_detail'),
    path('notifications/<int:pk>/mark-read/', views.notification_mark_read, name='notification_mark_read'),
    path('notifications/mark-all-read/', views.notification_mark_all_read, name='notification_mark_all_read'),
    path('notifications/<int:pk>/delete/', views.notification_delete, name='notification_delete'),
    path('sessions/<int:session_id>/create-reminder/', views.create_session_reminder, name='create_session_reminder'),
    
    # API endpoints
    path('api/overview/', views.api_overview, name='api_overview'),
    path('api/calendar-events/', views.api_calendar_events, name='api_calendar_events'),
    path('api/calendar/', views.api_calendar, name='api_calendar'),
    path('api/study-summary/', views.api_study_summary, name='api_study_summary'),
    path('api/session-durations/', views.api_session_durations, name='api_session_durations'),
    
    # Notification API endpoints
    path('api/notifications/', views.api_notifications, name='api_notifications'),
    path('api/notifications/counts/', views.api_notification_counts, name='api_notification_counts'),
    path('api/notifications/<int:pk>/mark-read/', views.api_mark_notification_read, name='api_mark_notification_read'),
    path('api/notifications/mark-all-read/', views.api_mark_all_notifications_read, name='api_mark_all_notifications_read'),
    path('api/notifications/<int:pk>/delete/', views.api_delete_notification, name='api_delete_notification'),
    path('api/notifications/create-reminder/', views.api_create_session_reminder, name='api_create_session_reminder'),
    
    # Session management API endpoints
    path('api/sessions/<int:session_id>/complete/', views.api_mark_session_completed, name='api_mark_session_completed'),
    path('api/sessions/upcoming/', views.api_upcoming_sessions, name='api_upcoming_sessions'),
]
