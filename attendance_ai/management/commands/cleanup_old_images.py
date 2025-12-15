# attendance_ai/management/commands/cleanup_old_images.py
from django.core.management.base import BaseCommand
from django.conf import settings
import os
from datetime import datetime, timedelta

class Command(BaseCommand):
    help = "Remove verification/uploaded images older than N days (default 30)"

    def add_arguments(self, parser):
        parser.add_argument("--days", type=int, default=30, help="Remove files older than DAYS")

    def handle(self, *args, **options):
        days = options["days"]
        cutoff = datetime.now() - timedelta(days=days)
        folder = os.path.join(settings.MEDIA_ROOT, "uploads")
        removed = 0
        if not os.path.exists(folder):
            self.stdout.write(self.style.WARNING("Uploads folder not found: %s" % folder))
            return
        for fname in os.listdir(folder):
            path = os.path.join(folder, fname)
            if os.path.isfile(path):
                mtime = datetime.fromtimestamp(os.path.getmtime(path))
                if mtime < cutoff:
                    try:
                        os.remove(path)
                        removed += 1
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f"Failed to remove {path}: {e}"))
        self.stdout.write(self.style.SUCCESS(f"Removed {removed} files older than {days} days"))
