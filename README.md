# Study Tracker - Hệ thống quản lý lịch học

Ứng dụng web Django để quản lý và theo dõi phiên học tập, tích hợp với Google Calendar để đồng bộ hóa tự động.

## Tính năng chính

- 📚 Quản lý phiên học tập (tạo, chỉnh sửa, xóa)
- 📅 Lịch trực quan hiển thị các phiên học
- 📊 Dashboard với thống kê và biểu đồ
- 🔔 Nhắc nhở qua Google Calendar
- 🔄 Đồng bộ tự động với Google Calendar
- 👤 Hệ thống đăng nhập/đăng ký user
- 📱 Giao diện responsive

## Yêu cầu hệ thống

- Python 3.8 trở lên
- pip (Python package manager)
- Tài khoản Google (để tích hợp Google Calendar)

## Hướng dẫn cài đặt từ đầu

### Bước 1: Chuẩn bị môi trường

1. **Tạo virtual environment:**
```bash
python -m venv venv
```

2. **Kích hoạt virtual environment:**
- Windows:
```bash
venv\Scripts\activate
```
- macOS/Linux:
```bash
source venv/bin/activate
```

### Bước 2: Cài đặt dependencies

1. **Tạo file `requirements.txt` với nội dung sau:**
```txt
# Core Django dependencies
Django==5.2.1
djangorestframework==3.15.2

# Environment configuration
python-decouple==3.8

# Google Calendar Integration
google-auth==2.28.2
google-auth-oauthlib==1.2.0
google-auth-httplib2==0.2.0
google-api-python-client==2.125.0

# Development and utilities
pytz==2024.1
```

2. **Cài đặt packages:**
```bash
pip install -r requirements.txt
```

### Bước 3: Tạo dự án Django

1. **Khởi tạo Django project:**
```bash
django-admin startproject study_tracker
cd study_tracker
```

2. **Tạo Django app:**
```bash
python manage.py startapp tracker
```

### Bước 4: Cấu hình Django Settings

1. **Chỉnh sửa file `study_tracker/settings.py`:**

```python
"""
Django settings for study_tracker project.
"""

from pathlib import Path
from decouple import config

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-3m*rlcuvry8e5ukq3h4nyt&#+9t5k-6xj@5*0q6!q8eq@)l!nu'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['studytracker.localhost', '127.0.0.1', 'localhost']

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'tracker',
    'rest_framework',  # Add Django REST framework
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'study_tracker.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'study_tracker.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    # Commented out for development ease
    # {
    #     'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    # },
    # {
    #     'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    # },
    # {
    #     'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    # },
    # {
    #     'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    # },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Ho_Chi_Minh'  # Vietnam timezone (UTC+7)
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Authentication settings
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'home'
LOGOUT_REDIRECT_URL = 'login'

# Google OAuth2 Settings
GOOGLE_OAUTH_CLIENT_ID = config('GOOGLE_OAUTH_CLIENT_ID', default='your-client-id-here')
GOOGLE_OAUTH_CLIENT_SECRET = config('GOOGLE_OAUTH_CLIENT_SECRET', default='your-client-secret-here')
GOOGLE_OAUTH_SCOPES = [
    'openid',
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile'
]

# Google Calendar Settings
GOOGLE_CALENDAR_REDIRECT_URI = 'http://localhost:8000/google-calendar/callback/'
```

### Bước 5: Cấu hình Google Calendar API

1. **Truy cập Google Cloud Console:**
   - Đi tới https://console.cloud.google.com/
   - Tạo project mới hoặc chọn project hiện có

2. **Kích hoạt Google Calendar API:**
   - Vào "APIs & Services" > "Library"
   - Tìm "Google Calendar API" và kích hoạt

3. **Tạo OAuth 2.0 credentials:**
   - Vào "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth 2.0 Client IDs"
   - Chọn "Web application"
   - Thêm Authorized redirect URIs: `http://localhost:8000/google-calendar/callback/`
   - Lưu Client ID và Client Secret

4. **Tạo file `.env` trong thư mục `study_tracker/`:**
```env
# Google OAuth2 Settings
GOOGLE_OAUTH_CLIENT_ID=your-actual-client-id-here
GOOGLE_OAUTH_CLIENT_SECRET=your-actual-client-secret-here
```

### Bước 6: Tạo Models

1. **Tạo file `tracker/models.py`:**

```python
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
    
    def __str__(self):
        return f"{self.title} - {self.user.username}"
```

### Bước 7: Tạo Google Calendar Service

#### Bước 7.1: Tạo file `tracker/google_calendar_service.py`:

```python
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
                    'overrides': [
                        {'method': 'email', 'minutes': 24 * 60},  # 1 day before
                        {'method': 'popup', 'minutes': 30},        # 30 minutes before
                    ],
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
```

#### Bước 7.2: Tự động đồng bộ với Google Calendar

Hệ thống Study Tracker đã được tích hợp **đầy đủ** tính năng tự động đồng bộ với Google Calendar. Dưới đây là chi tiết về cách thức hoạt động:

#### 1. Tự động đồng bộ khi tạo/sửa Study Session ✅

**Khi tạo session mới:**
- Hệ thống tự động kiểm tra nếu người dùng đã bật tùy chọn "sync_to_google"
- Nếu có kết nối Google Calendar và sync được bật, session sẽ tự động được tạo trên Google Calendar
- Thông báo thành công/thất bại sẽ hiển thị cho người dùng

**Code implementation trong `session_create` view:**
```python
@login_required
def session_create(request):
    if request.method == 'POST':
        form = StudySessionForm(request.POST)
        if form.is_valid():
            session = form.save(commit=False)
            session.user = request.user
            session.save()
            
            # Auto sync to Google Calendar if enabled
            if session.sync_to_google:
                try:
                    integration = GoogleCalendarIntegration.objects.get(user=request.user, sync_enabled=True)
                    service = GoogleCalendarService()
                    success, message = service.sync_session(request.user, session)
                    
                    if success:
                        messages.success(request, 'Study session created and synced to Google Calendar!')
                    else:
                        messages.warning(request, f'Study session created but sync failed: {message}')
                except GoogleCalendarIntegration.DoesNotExist:
                    messages.warning(request, 'Study session created but Google Calendar is not connected.')
            else:
                messages.success(request, 'Study session created successfully!')
                
            return redirect('session_list')
```

**Khi sửa session:**
- Hệ thống so sánh trạng thái sync cũ và mới
- Tự động cập nhật hoặc tạo mới event trên Google Calendar nếu cần
- Xóa event khỏi Google Calendar nếu sync bị tắt

#### 2. Tính năng Sync All Sessions ✅

**Chức năng `google_calendar_sync_all` đã được implement hoàn chỉnh:**

```python
@login_required
def google_calendar_sync_all(request):
    try:
        # Check if user has Google Calendar integration
        integration = GoogleCalendarIntegration.objects.get(user=request.user, sync_enabled=True)
        
        # Get all sessions with sync enabled
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
                print(f"Sync error for session {session.id}: {message}")
        
        # Display appropriate success/error messages
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
```

#### 3. Smart Sync Method trong GoogleCalendarService ✅

**Phương thức `sync_session` thông minh:**
```python
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
```

#### 4. Các tính năng đồng bộ đã implement:

**a) Create Calendar Event:** ✅
- Tạo event mới trên Google Calendar
- Lưu Google event ID vào database
- Thiết lập reminder (email 1 ngày trước, popup 30 phút trước)

**b) Update Calendar Event:** ✅
- Cập nhật event hiện có
- Tự động tạo mới nếu event không tồn tại
- Cập nhật timestamp last_synced

**c) Delete Calendar Event:** ✅
- Xóa event khỏi Google Calendar
- Xóa Google event ID khỏi database
- Xử lý trường hợp event đã bị xóa

**d) Toggle Session Sync:** ✅
- Bật/tắt sync cho từng session riêng biệt
- Tự động sync ngay khi bật
- AJAX response cho UI real-time

#### 5. Automatic Sync Features - HOÀN THÀNH:

✅ **Tự động sync khi tạo session mới** - IMPLEMENTED
✅ **Tự động sync khi sửa session** - IMPLEMENTED  
✅ **Sync all sessions** - IMPLEMENTED
✅ **Tự động xóa event khi xóa session** - IMPLEMENTED
✅ **Smart sync dựa trên trạng thái session** - IMPLEMENTED
✅ **Error handling và user feedback** - IMPLEMENTED
✅ **Token refresh tự động** - IMPLEMENTED

#### 6. Cách sử dụng tính năng đồng bộ:

1. **Kết nối Google Calendar:**
   - Vào Settings > Google Calendar
   - Click "Connect to Google Calendar"
   - Authorize ứng dụng

2. **Tạo session với sync:**
   - Tích chọn "Sync to Google Calendar" khi tạo session
   - Session sẽ tự động được tạo trên Google Calendar

3. **Sync tất cả sessions:**
   - Vào Google Calendar Settings
   - Click "Sync All Sessions to Google Calendar"
   - Tất cả sessions có sync enabled sẽ được đồng bộ

4. **Toggle sync cho session riêng lẻ:**
   - Trong danh sách sessions, click toggle sync button
   - Session sẽ tự động sync/unsync ngay lập tức

#### 7. Error Handling và Logging:

- **Token expired:** Tự động refresh token
- **Event not found:** Tự động tạo mới
- **API errors:** Log chi tiết và thông báo user
- **Network errors:** Graceful fallback và retry logic

#### 8. Implementation Details:

**GoogleCalendarService Methods hoàn chỉnh:**

1. `create_calendar_event()` - Tạo event mới
2. `update_calendar_event()` - Cập nhật event
3. `delete_calendar_event()` - Xóa event
4. `sync_session()` - Smart sync dựa trên trạng thái
5. `get_credentials()` - Lấy và refresh credentials
6. `handle_oauth_callback()` - Xử lý OAuth flow

**Views với automatic sync:**

1. `session_create()` - Auto sync khi tạo
2. `session_edit()` - Auto sync khi sửa
3. `session_delete()` - Auto delete từ calendar
4. `google_calendar_sync_all()` - Sync tất cả sessions
5. `toggle_session_sync()` - AJAX toggle sync

### Bước 8: Tạo Admin Configuration

1. **Chỉnh sửa file `tracker/admin.py`:**

```python
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
```

### Bước 9: Tạo và chạy Migrations

1. **Tạo migrations:**
```bash
python manage.py makemigrations tracker
```

2. **Chạy migrations:**
```bash
python manage.py migrate
```

### Bước 10: Tạo Superuser

```bash
python manage.py createsuperuser
```

### Bước 11: Cấu hình URLs

1. **Tạo file `tracker/urls.py`:**

```python
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
    
    # API endpoints
    path('api/overview/', views.api_overview, name='api_overview'),
    path('api/calendar-events/', views.api_calendar_events, name='api_calendar_events'),
    path('api/calendar/', views.api_calendar, name='api_calendar'),
    path('api/study-summary/', views.api_study_summary, name='api_study_summary'),
]
```

2. **Chỉnh sửa file `study_tracker/urls.py`:**

```python
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('tracker.urls')),
]
```

### Bước 12: Tạo Base Views và Forms

1. **Tạo file `tracker/forms.py`:**

```python
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import StudySession

class StudySessionForm(forms.ModelForm):
    class Meta:
        model = StudySession
        fields = ['subject', 'description', 'study_date', 'start_time', 'end_time', 'status', 'sync_to_google']
        widgets = {
            'study_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'start_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'end_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'subject': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }

class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user
```

### Bước 13: Tạo Basic Views

1. **Tạo file `tracker/views.py` cơ bản:**

```python
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import StudySession, GoogleCalendarIntegration
from .forms import StudySessionForm, UserRegistrationForm
from .google_calendar_service import GoogleCalendarService
import secrets

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
            return redirect('session_list')
    else:
        form = StudySessionForm()
    return render(request, 'tracker/session_form.html', {'form': form})

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
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}!')
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
    
    request.session.pop('google_oauth_state', None)
    
    service = GoogleCalendarService()
    success, message = service.handle_oauth_callback(request.user, code, state)
    
    if success:
        messages.success(request, message)
    else:
        messages.error(request, message)
    
    return redirect('google_calendar_settings')

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_calendar(request):
    sessions = StudySession.objects.filter(user=request.user)
    data = []
    for session in sessions:
        data.append({
            'id': session.id,
            'title': session.subject,
            'start': f"{session.study_date}T{session.start_time}",
            'end': f"{session.study_date}T{session.end_time}",
            'description': session.description,
            'status': session.status,
        })
    return Response(data)
```

### Bước 14: Tạo Templates cơ bản

1. **Tạo thư mục templates:**
```bash
mkdir templates
mkdir templates/tracker
```

2. **Tạo file `templates/base.html`:**

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Study Tracker{% endblock %}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
        <div class="container">
            <a class="navbar-brand" href="{% url 'home' %}">Study Tracker</a>
            <div class="navbar-nav ms-auto">
                {% if user.is_authenticated %}
                    <a class="nav-link" href="{% url 'dashboard' %}">Dashboard</a>
                    <a class="nav-link" href="{% url 'session_list' %}">Sessions</a>
                    <a class="nav-link" href="{% url 'calendar' %}">Calendar</a>
                    <a class="nav-link" href="{% url 'user_logout' %}">Logout</a>
                {% else %}
                    <a class="nav-link" href="{% url 'login' %}">Login</a>
                    <a class="nav-link" href="{% url 'user_register' %}">Register</a>
                {% endif %}
            </div>
        </div>
    </nav>

    <div class="container mt-4">
        {% if messages %}
            {% for message in messages %}
                <div class="alert alert-{{ message.tags }} alert-dismissible fade show">
                    {{ message }}
                    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                </div>
            {% endfor %}
        {% endif %}

        {% block content %}
        {% endblock %}
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    {% block extra_js %}{% endblock %}
</body>
</html>
```

3. **Tạo file `templates/tracker/login.html`:**

```html
{% extends 'base.html' %}

{% block title %}Login - Study Tracker{% endblock %}

{% block content %}
<div class="row justify-content-center">
    <div class="col-md-6">
        <div class="card">
            <div class="card-header">
                <h4>Login</h4>
            </div>
            <div class="card-body">
                <form method="post">
                    {% csrf_token %}
                    <div class="mb-3">
                        <label for="username" class="form-label">Username</label>
                        <input type="text" class="form-control" name="username" required>
                    </div>
                    <div class="mb-3">
                        <label for="password" class="form-label">Password</label>
                        <input type="password" class="form-control" name="password" required>
                    </div>
                    <button type="submit" class="btn btn-primary">Login</button>
                    <a href="{% url 'user_register' %}" class="btn btn-link">Don't have an account? Register</a>
                </form>
            </div>
        </div>
    </div>
</div>
{% endblock %}
```

### Bước 15: Chạy server và test

1. **Chạy development server:**
```bash
python manage.py runserver
```

2. **Truy cập ứng dụng:**
   - Mở trình duyệt và vào: http://127.0.0.1:8000
   - Đăng ký tài khoản mới hoặc đăng nhập với superuser

3. **Test admin panel:**
   - Vào: http://127.0.0.1:8000/admin
   - Đăng nhập với superuser account

## Cấu trúc thư mục hoàn chỉnh

```
study_tracker_project/
├── venv/                       # Virtual environment
├── study_tracker/              # Django project root
│   ├── manage.py
│   ├── db.sqlite3             # SQLite database
│   ├── .env                   # Environment variables
│   ├── study_tracker/         # Project settings
│   │   ├── __init__.py
│   │   ├── settings.py
│   │   ├── urls.py
│   │   ├── wsgi.py
│   │   └── asgi.py
│   ├── tracker/               # Main app
│   │   ├── __init__.py
│   │   ├── admin.py
│   │   ├── apps.py
│   │   ├── models.py
│   │   ├── views.py
│   │   ├── forms.py
│   │   ├── urls.py
│   │   ├── google_calendar_service.py
│   │   ├── migrations/
│   │   └── tests.py
│   └── templates/             # HTML templates
│       ├── base.html
│       └── tracker/
│           ├── login.html
│           ├── dashboard.html
│           ├── session_list.html
│           └── ...
└── requirements.txt
```

## Tính năng nâng cao cần thêm

Để có đầy đủ tính năng như dự án gốc, bạn cần thêm:

1. **Dashboard với charts:** Sử dụng Chart.js để hiển thị thống kê
2. **Calendar integration:** FullCalendar.js cho view lịch
3. **Responsive templates:** Bootstrap components cho UI đẹp
4. **REST API endpoints:** Để hỗ trợ AJAX calls
5. **Error handling:** Xử lý lỗi toàn diện
6. **Session management:** CRUD operations đầy đủ
7. **Notification system:** Thông báo trong app

## Debugging và Troubleshooting

### Lỗi thường gặp:

1. **ImportError: No module named 'decouple'**
   ```bash
   pip install python-decouple
   ```

2. **Google API errors:**
   - Kiểm tra Client ID và Client Secret
   - Đảm bảo redirect URI chính xác
   - Kích hoạt Google Calendar API

3. **Database errors:**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

4. **Static files not loading:**
   ```bash
   python manage.py collectstatic
   ```

## Triển khai Production

1. **Cập nhật settings.py:**
   - Set `DEBUG = False`
   - Cập nhật `ALLOWED_HOSTS`
   - Sử dụng PostgreSQL thay vì SQLite

2. **Environment variables:**
   - Sử dụng `.env` file cho production
   - Không commit credentials vào git

3. **Security checklist:**
   - Đổi SECRET_KEY
   - Cấu hình HTTPS
   - Setup proper firewall rules

## Liên hệ hỗ trợ

Nếu gặp vấn đề trong quá trình cài đặt, vui lòng kiểm tra:
1. Python version (>= 3.8)
2. Virtual environment đã được kích hoạt
3. Tất cả dependencies đã được cài đặt
4. Google Calendar API credentials đã đúng