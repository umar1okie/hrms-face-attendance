#attendance_ai/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from .utils.crypto import encrypt_array, decrypt_array


# ---------------------------------------------------------
# MAIN USER MODEL (AUTH_USER_MODEL)
# ---------------------------------------------------------
class RegisteredUser(AbstractUser):
    employee_id = models.CharField(max_length=64, unique=True)
    department = models.CharField(max_length=128, null=True, blank=True)
    designation = models.CharField(max_length=128, null=True, blank=True)
    is_remote_worker = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.username} ({self.employee_id})"


# ---------------------------------------------------------
# FACE PROFILE (ONE PER USER)
# ---------------------------------------------------------
class FaceProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="face_profile"
    )

    face_encoding = models.JSONField(null=True, blank=True)
    encoding_version = models.CharField(max_length=20, default="v1")

    consent_given = models.BooleanField(default=False)
    consent_date = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    # encryption helpers
    def set_encoding(self, arr):
        if arr is None:
            self.face_encoding = None
        else:
            arr_list = arr.tolist() if hasattr(arr, "tolist") else arr
            self.face_encoding = encrypt_array(arr_list)

    def get_encoding(self):
        if not self.face_encoding:
            return None
        return decrypt_array(self.face_encoding)

    encoding = property(get_encoding, set_encoding)


# ---------------------------------------------------------
# ATTENDANCE RECORD
# ---------------------------------------------------------
class RemoteAttendance(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="attendance_records"
    )

    check_in_time = models.DateTimeField(null=True, blank=True)
    check_out_time = models.DateTimeField(null=True, blank=True)

    status = models.CharField(max_length=20, default='pending')
    confidence_score = models.FloatField(null=True, blank=True)

    geolocation = models.JSONField(null=True, blank=True)
    device_info = models.JSONField(null=True, blank=True)
    verification_image_url = models.URLField(null=True, blank=True)

    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='reviewed_attendance'
    )

    review_notes = models.TextField(null=True, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)


# ---------------------------------------------------------
# ATTENDANCE ANOMALY
# ---------------------------------------------------------
class AttendanceAnomaly(models.Model):
    attendance = models.ForeignKey(RemoteAttendance, on_delete=models.CASCADE)
    anomaly_type = models.CharField(max_length=50)
    severity = models.CharField(max_length=10)
    description = models.TextField()

    detected_at = models.DateTimeField(auto_now_add=True)
    resolved = models.BooleanField(default=False)


# ---------------------------------------------------------
# AUDIT LOG
# ---------------------------------------------------------
class AuditLog(models.Model):
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )

    action = models.CharField(max_length=100)
    target_repr = models.CharField(max_length=255, blank=True)
    extra = models.JSONField(null=True, blank=True)

    ip_address = models.CharField(max_length=45, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-timestamp"]




