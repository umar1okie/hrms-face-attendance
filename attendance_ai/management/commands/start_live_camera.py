from django.core.management.base import BaseCommand
import numpy as np
import time
from attendance_ai.services.live_camera import LiveAttendanceEngine, start_camera_realtime
from attendance_ai.models import FaceProfile, RemoteAttendance  # adjust names if different
from django.contrib.auth import get_user_model

User = get_user_model()

# You may adjust what RemoteAttendance fields you set on check-in
class Command(BaseCommand):
    help = "Start live camera and auto-mark attendance for matched users."

    def add_arguments(self, parser):
        parser.add_argument("--show", action="store_true", help="Show live camera window (default True).")
        parser.add_argument("--min-interval", type=int, default=60, help="Min seconds between punches per user.")

    def handle(self, *args, **options):
        show_window = options.get("show", True)
        min_interval = options.get("min_interval", 60)

        # Load embeddings from DB
        profiles = FaceProfile.objects.filter(is_active=True).select_related("user")
        known_embeddings = {}
        user_meta = {}
        for p in profiles:
            if not p.face_encoding:  # skip empty
                continue
            try:
                emb = np.array(p.face_encoding, dtype=np.float32)
            except Exception:
                # if stored as string, try eval() or json loads (be cautious)
                continue
            if emb is None or emb.size == 0:
                continue
            known_embeddings[p.user_id] = emb
            user_meta[p.user_id] = {"username": getattr(p.user, "username", str(p.user_id))}

        if not known_embeddings:
            self.stdout.write(self.style.WARNING("No known embeddings found in FaceProfile. Seed at least one."))
            return

        # create engine and override interval
        engine = LiveAttendanceEngine(known_embeddings, user_meta)
        # override config
        from attendance_ai.services.live_camera import MIN_SECONDS_BETWEEN_PUNCHES
        # monkey patch minimal interval
        import attendance_ai.services.live_camera as lc
        lc.MIN_SECONDS_BETWEEN_PUNCHES = min_interval

        self.stdout.write(self.style.SUCCESS(f"Loaded {len(known_embeddings)} face profiles. Starting camera..."))
        punches = start_camera_realtime(engine, show_window=show_window)

        # Persist punches to DB
        for p in punches:
            uid = p["user_id"]
            conf = float(p["conf"])
            dist = float(p["dist"])
            ts = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(p["timestamp"]))
            # Create a simple attendance entry: check_in_time now
            # Adjust fields to match your RemoteAttendance model
            try:
                user = User.objects.get(pk=uid)
            except User.DoesNotExist:
                continue

            # Decide logic: create a new RemoteAttendance if today's not present or add check_out.
            # Simple approach: always create a "check-in" record with status 'verified'
            a = RemoteAttendance.objects.create(
                user=user,
                check_in_time=time.strftime("%Y-%m-%d %H:%M:%S"),
                status="verified",
                confidence_score=conf
            )
            self.stdout.write(self.style.SUCCESS(f"Marked attendance for {user} at {ts} (conf={conf:.2f}, dist={dist:.2f})"))

        self.stdout.write(self.style.SUCCESS("Camera session ended."))
