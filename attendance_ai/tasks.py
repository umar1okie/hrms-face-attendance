# attendance_ai/tasks.py

import os
import numpy as np
from datetime import timedelta
from celery import shared_task
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings

from .models import RemoteAttendance, FaceProfile, AttendanceAnomaly
from .services.face_recognition import FaceRecognitionService


# -------------------------------------------------------------------
# 1. FACE VERIFICATION (async check after check-in)
# -------------------------------------------------------------------

@shared_task
def process_face_verification(attendance_id, new_image_path):
    """
    Re-process attendance verification in background:
    - Extract face encoding from image
    - Compare with stored encoding
    - Update status & confidence_score
    - Trigger anomaly detection
    """

    try:
        attendance = RemoteAttendance.objects.get(id=attendance_id)
    except RemoteAttendance.DoesNotExist:
        return {"status": "error", "message": "Attendance record not found"}

    # extract embedding
    new_emb = FaceRecognitionService.extract_face_encoding(new_image_path)
    if new_emb is None:
        attendance.status = "no_face_detected"
        attendance.save()
        return {"status": "error", "message": "No face detected"}

    # load stored embedding
    try:
        profile = FaceProfile.objects.get(user=attendance.user, is_active=True)
    except FaceProfile.DoesNotExist:
        attendance.status = "profile_missing"
        attendance.save()
        return {"status": "error", "message": "No profile found"}

    stored_emb = np.array(profile.face_encoding, dtype=np.float32)

    confidence = FaceRecognitionService.calculate_confidence(stored_emb, new_emb)

    attendance.confidence_score = float(confidence)

    if confidence < 0.65:
        attendance.status = "unverified"
    else:
        attendance.status = "verified"

    attendance.save()

    # run anomaly check async
    detect_attendance_anomalies.delay(attendance.id)

    return {"status": "success", "confidence": float(confidence)}


# -------------------------------------------------------------------
# 2. ANOMALY DETECTION
# -------------------------------------------------------------------

@shared_task
def detect_attendance_anomalies(attendance_id):
    """
    Detect anomalies such as:
    - Low confidence score
    - Odd geolocation
    - Suspicious device
    - Too frequent check-ins
    """

    try:
        attendance = RemoteAttendance.objects.get(id=attendance_id)
    except RemoteAttendance.DoesNotExist:
        return {"status": "error", "message": "not found"}

    anomalies = []

    # 1. confidence anomaly
    if attendance.confidence_score and attendance.confidence_score < 0.50:
        anomalies.append(("low_confidence", "Very low face match confidence", "high"))

    # 2. impossible geolocation (optional)
    geo = attendance.geolocation or {}
    if geo.get("lat") is None or geo.get("lng") is None:
        anomalies.append(("missing_geolocation", "No geolocation provided", "medium"))

    # 3. too many checkins
    last_hour = RemoteAttendance.objects.filter(
        user=attendance.user,
        check_in_time__gte=timezone.now() - timedelta(hours=1)
    ).count()

    if last_hour > 5:  # suspicious
        anomalies.append(("suspicious_frequency", "Too many check-ins within 1 hour", "high"))

    # save anomalies
    for code, msg, severity in anomalies:
        AttendanceAnomaly.objects.create(
            attendance=attendance,
            anomaly_type=code,
            description=msg,
            severity=severity
        )

    # notify admin on severe anomalies
    if any(a[2] == "high" for a in anomalies):
        send_mail(
            subject="⚠ High Severity Attendance Anomaly Detected",
            message=f"User {attendance.user.username} triggered anomalies.\nAttendance ID: {attendance.id}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.ADMIN_EMAIL],
            fail_silently=True,
        )

    return {"status": "ok", "anomalies": len(anomalies)}


# -------------------------------------------------------------------
# 3. CLEANUP OLD IMAGES (every night)
# -------------------------------------------------------------------

@shared_task
def cleanup_old_images(days=30):
    """
    Delete attendance verification images older than X days.
    """

    cutoff = timezone.now() - timedelta(days=days)
    old_records = RemoteAttendance.objects.filter(
        check_in_time__lt=cutoff,
        verification_image_url__isnull=False
    )

    deleted = 0
    for rec in old_records:
        file_path = rec.verification_image_url.replace("/media", settings.MEDIA_ROOT)
        if os.path.exists(file_path):
            os.remove(file_path)
            deleted += 1

    return {"deleted_images": deleted}


# -------------------------------------------------------------------
# 4. DAILY REPORTS
# -------------------------------------------------------------------

@shared_task
def generate_daily_reports():
    """
    Send daily attendance summary email to HR.
    """

    today = timezone.now().date()
    records = RemoteAttendance.objects.filter(
        check_in_time__date=today
    )

    total = records.count()
    verified = records.filter(status="verified").count()
    unverified = records.filter(status="unverified").count()

    msg = (
        f"Daily Attendance Report\n\n"
        f"Date: {today}\n"
        f"Total Check-ins: {total}\n"
        f"Verified: {verified}\n"
        f"Unverified: {unverified}\n\n"
        f"HRMS AI Attendance System"
    )

    send_mail(
        subject=f"Daily Attendance Report – {today}",
        message=msg,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[settings.HR_TEAM_EMAIL],
        fail_silently=True,
    )

    return {"report_sent": True, "total": total}
