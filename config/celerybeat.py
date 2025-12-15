#config/celerybeat.py
from celery.schedules import crontab

app.conf.beat_schedule = {
    "cleanup-old-images-daily": {
        "task": "attendance_ai.tasks.cleanup_old_images",
        "schedule": crontab(hour=3, minute=0),  # 3 AM daily
    },
    "daily-attendance-report": {
        "task": "attendance_ai.tasks.generate_daily_reports",
        "schedule": crontab(hour=18, minute=0),  # 6 PM daily
    },
}
