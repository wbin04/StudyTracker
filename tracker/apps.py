from django.apps import AppConfig
import os


class TrackerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tracker'
    
    def ready(self):
        # Only start scheduler in the main process (not during migrations, etc.)
        if os.environ.get('RUN_MAIN') or not os.environ.get('RUN_MAIN'):
            try:
                from .scheduler import start_scheduler
                start_scheduler()
                print("Scheduler started successfully in apps.py")
            except Exception as e:
                print(f"Failed to start scheduler: {e}")
