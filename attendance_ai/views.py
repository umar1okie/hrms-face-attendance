# attendance_ai/views.py
import os
import uuid
import numpy as np
from django.conf import settings
from django.utils import timezone
from django.core.files.storage import default_storage
from django.contrib.auth import get_user_model
import requests

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status, permissions

from .serializers import (
    FaceRegisterSerializer,
    AttendanceCheckinSerializer,
    UserRegisterSerializer,
    AttendanceRecordSerializer
)

from .models import FaceProfile, RemoteAttendance, AuditLog
from .services.face_recognition import FaceRecognitionService
from .tasks import process_face_verification
from .utils.validators import validate_image_file
from .utils.audit import audit_action
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from django.contrib.auth import authenticate
from .models import RegisteredUser
from .serializers import AttendanceCheckinSerializer
from django.utils.timezone import now
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone


User = get_user_model()



# --------------------------
# File Saving Helper
# --------------------------
def save_uploaded_image(f):
    folder = os.path.join(settings.MEDIA_ROOT, "uploads")
    os.makedirs(folder, exist_ok=True)

    filename = f"{uuid.uuid4().hex}.jpg"
    path = os.path.join(folder, filename)

    with open(path, "wb") as out:
        for chunk in f.chunks():
            out.write(chunk)

    return path, f"/media/uploads/{filename}"


# --------------------------
# Face Register View
# --------------------------
class FaceRegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = FaceRegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        data = serializer.validated_data
        image = data.pop("image")

        # ---------------------------
        # 1. SAVE IMAGE
        # ---------------------------
        saved_path, public_url = save_uploaded_image(image)

        # ---------------------------
        # 2. FACE ENCODING
        # ---------------------------
        emb = FaceRecognitionService.extract_face_encoding(saved_path)
        if emb is None:
            return Response({"status": "error", "message": "No face detected"}, status=400)

        # Normalize encoding
        if isinstance(emb, np.ndarray):
            emb = emb.tolist()

        # ---------------------------
        # 3. CREATE OR UPDATE USER
        # ---------------------------
        employee_id = data.get("employee_id")
        username = data.get("username") or employee_id
        password = None

        # password = data.get("password") or User.objects.make_random_password()

        user, created = User.objects.get_or_create(
            employee_id=employee_id,
            defaults={
                "username": username,
                "email": data.get("email", ""),
                "first_name": data.get("first_name", ""),
                "last_name": data.get("last_name", ""),
                "department": data.get("department", ""),
                "designation": data.get("designation", ""),
                "is_remote_worker": data.get("is_remote_worker", True),
            },
        )

        if created:
            user.set_password(password)
            user.save()
        else:
            # Update if fields provided
            for k in ("username", "email", "first_name", "last_name",
                      "department", "designation", "is_remote_worker"):
                if data.get(k) not in (None, ""):
                    setattr(user, k, data.get(k))

            if password:
                user.set_password(password)

            user.save()

        # ---------------------------
        # 4. SAVE FACE PROFILE
        # ---------------------------
        FaceProfile.objects.update_or_create(
            user=user,
            defaults={
                "face_encoding": emb,
                "encoding_version": "insightface_v1",
                "consent_given": True,
                "is_active": True,
            }
        )

        # ---------------------------
        # 5. AUDIT LOG ENTRY
        # ---------------------------
        AuditLog.objects.create(
            actor=None,  # registration API has no authenticated actor
            action="face_registered",
            target_repr=f"User:{user.id}",
            extra={
                "employee_id": user.employee_id,
                "image_url": public_url,
                "encoding_version": "insightface_v1",
            },
            ip_address=request.META.get("REMOTE_ADDR")
        )

        # ---------------------------
        # 6. RESPONSE
        # ---------------------------
        return Response({
            "status": "success",
            "message": "Face registered successfully",
            "user_id": user.id,
            "employee_id": user.employee_id,
            "username": user.username,
            "image_url": public_url
        })



# --------------------------
# Attendance Check-in View
# --------------------------
# --------------------------
# Attendance Check-in View
# --------------------------
class AttendanceCheckinView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = AttendanceCheckinSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        image = serializer.validated_data.get("image")
        geolocation = serializer.validated_data.get("geolocation", {})
        device_info = serializer.validated_data.get("device_info", {})

        # --------------------------------------------------
        # 1. Save uploaded image
        # --------------------------------------------------
        saved_path, public_url = save_uploaded_image(image)

        # --------------------------------------------------
        # 2. Extract face embedding
        # --------------------------------------------------
        embedding = FaceRecognitionService.extract_face_encoding(saved_path)
        if embedding is None:
            return Response(
                {"status": "error", "message": "No face detected"},
                status=400
            )

        # --------------------------------------------------
        # 3. Compare with stored face profiles
        # --------------------------------------------------
        profiles = FaceProfile.objects.filter(
            is_active=True
        ).exclude(face_encoding__isnull=True)

        best_score = -1.0
        best_profile = None

        for profile in profiles:
            stored_embedding = np.array(profile.face_encoding, dtype=np.float32)
            score = FaceRecognitionService.calculate_confidence(
                stored_embedding, embedding
            )

            if score > best_score:
                best_score = score
                best_profile = profile

        # --------------------------------------------------
        # 4. Thresholds
        # --------------------------------------------------
        MATCH_THRESHOLD = 0.65        # Face belongs to a user
        AUTO_APPROVE_THRESHOLD = 0.80 # Auto verified (no admin)

        if not best_profile or best_score < MATCH_THRESHOLD:
            return Response(
                {
                    "status": "not_found",
                    "message": "Face not registered",
                    "best_score": float(best_score) if best_score >= 0 else None,
                    "image_url": public_url,
                },
                status=404
            )

        # --------------------------------------------------
        # 5. Decide attendance status
        # --------------------------------------------------
        attendance_status = (
            "verified"
            if best_score >= AUTO_APPROVE_THRESHOLD
            else "pending"
        )

        user = best_profile.user

        attendance = RemoteAttendance.objects.create(
            user=user,
            check_in_time=timezone.now(),
            status=attendance_status,
            confidence_score=float(best_score),
            geolocation=geolocation,
            device_info=device_info,
            verification_image_url=public_url,
        )

        # --------------------------------------------------
        # 6. Audit log
        # --------------------------------------------------
        AuditLog.objects.create(
            actor=request.user if request.user.is_authenticated else None,
            action="attendance_checkin",
            target_repr=f"user:{user.id}",
            extra={
                "confidence": float(best_score),
                "status": attendance_status,
            },
            ip_address=request.META.get("REMOTE_ADDR"),
        )

        # --------------------------------------------------
        # 7. Async verification task
        # --------------------------------------------------
        process_face_verification.delay(attendance.id, saved_path)

        # --------------------------------------------------
        # 8. Response
        # --------------------------------------------------
        return Response(
            {
                "status": "success",
                "attendance_status": attendance_status,
                "confidence_score": float(best_score),
                "attendance_id": attendance.id,
                "check_in_time": attendance.check_in_time,
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "employee_id": user.employee_id,
                    "name": f"{user.first_name} {user.last_name}".strip(),
                },
                "image_url": public_url,
            },
            status=200,
        )

    
# --------------------------
# User Registration View
# --------------------------
class UserRegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = UserRegisterSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        user = serializer.save()

        # Already handled inside serializer → RegisteredUser created

        return Response({
            "status": "success",
            "message": "User registered successfully",
            "username": user.username,
            "employee_id": user.employee_id,
            "email": user.email,
        }, status=201)

    

# --------------------------
# Simple Authentication Views
# --------------------------
    
@api_view(['POST'])
@permission_classes([AllowAny])
def login_user(request):
    username = request.data.get("username")
    password = request.data.get("password")

    if not username or not password:
        return Response({"error": "Username and password are required"}, status=400)

    user = authenticate(username=username, password=password)

    if user is None:
        return Response({"error": "Invalid credentials"}, status=401)

    return Response({
        "message": "Login successful",
        "user": {
            "id": user.id,
            "username": user.username,
            "employee_id": user.employee_id,
            "email": user.email,
        }
    }, status=200)


@api_view(['POST'])
@permission_classes([AllowAny])
def register_user(request):
    username = request.data.get("username")
    password = request.data.get("password")
    employee_id = request.data.get("employee_id")

    if not username or not password or not employee_id:
        return Response({"error": "username, password, employee_id required"}, status=400)

    if User.objects.filter(username=username).exists():
        return Response({"error": "Username already exists"}, status=400)

    if User.objects.filter(employee_id=employee_id).exists():
        return Response({"error": "Employee ID already exists"}, status=400)

    user = User(
        username=username,
        employee_id=employee_id,
        email=request.data.get("email", "")
    )

    user.set_password(password)
    user.save()

    return Response({
        "message": "User registered",
        "user": {
            "id": user.id,
            "username": user.username,
            "employee_id": user.employee_id,
        }
    }, status=201)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def attendance_history(request):
    records = RemoteAttendance.objects.filter(
        user=request.user
    ).order_by("-check_in_time")

    serializer = AttendanceRecordSerializer(records, many=True)
    return Response(serializer.data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def today_status(request):
    today = timezone.now().date()

    record = RemoteAttendance.objects.filter(
        user=request.user,
        check_out_time__isnull=True,
        check_in_time__date=today
    ).order_by("-check_in_time").first()


    if record:
        return Response({
            "checked_in": True,
            "check_in_time": record.check_in_time,
            "checked_out": bool(record.check_out_time),
            "check_out_time": record.check_out_time
        })

    return Response({"checked_in": False})



class AttendanceCheckoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user

        attendance = (
            RemoteAttendance.objects
            .filter(user=user, check_out_time__isnull=True)
            .order_by("-check_in_time")
            .first()
        )

        if not attendance:
            return Response(
                {
                    "status": "error",
                    "message": "No active check-in found"
                },
                status=status.HTTP_404_NOT_FOUND
            )

        attendance.check_out_time = timezone.now()
        attendance.save(update_fields=["check_out_time"])

        # Audit log
        AuditLog.objects.create(
            actor=user,
            action="attendance_checkout",
            target_repr=f"user:{user.id}",
            extra={
                "attendance_id": attendance.id
            },
            ip_address=request.META.get("REMOTE_ADDR"),
        )

        return Response(
            {
                "status": "success",
                "message": "Checkout successful",
                "check_out_time": attendance.check_out_time,
            },
            status=status.HTTP_200_OK
        )
