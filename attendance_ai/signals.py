# attendance_ai/signals.py
from django.dispatch import receiver
from django.db.models.signals import post_save
from .models import RemoteAttendance, AuditLog

@receiver(post_save, sender=RemoteAttendance)
def attendance_post_save(sender, instance, created, **kwargs):
    if created:
        AuditLog.objects.create(
            actor=None,  # you can pass request.user via view when calling explicitly
            action="attendance_created",
            target_repr=f"RemoteAttendance:{instance.id}",
            extra={"status": instance.status, "confidence_score": instance.confidence_score}
        )
