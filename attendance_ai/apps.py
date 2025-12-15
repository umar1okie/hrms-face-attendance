from django.apps import AppConfig


class AttendanceAiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'attendance_ai'

    def ready(self):
        import attendance_ai.signals
