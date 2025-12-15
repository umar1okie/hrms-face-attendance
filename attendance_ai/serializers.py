# attendance_ai/serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import FaceProfile, RemoteAttendance
from .models import RegisteredUser


User = get_user_model()

class UserRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = RegisteredUser
        fields = ["id", "username", "email", "password", "employee_id"]
        extra_kwargs = {
            "password": {"write_only": True}
        }

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = RegisteredUser(**validated_data)
        user.set_password(password)
        user.save()
        return user

class FaceRegisterSerializer(serializers.Serializer):
    # multipart/form-data
    username = serializers.CharField(required=False)
    email = serializers.EmailField(required=False)
    first_name = serializers.CharField(required=False)
    last_name = serializers.CharField(required=False)
    employee_id = serializers.CharField(required=True)
    department = serializers.CharField(required=False, allow_blank=True)
    designation = serializers.CharField(required=False, allow_blank=True)
    is_remote_worker = serializers.BooleanField(required=False, default=True)
    password = serializers.CharField(required=False, write_only=True)
    image = serializers.ImageField()

class AttendanceCheckinSerializer(serializers.Serializer):
    """Used only for POST check-in requests"""
    image = serializers.ImageField(required=True)
    geolocation = serializers.JSONField(required=False)
    device_info = serializers.JSONField(required=False)

class AttendanceRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = RemoteAttendance
        fields = [
            "id",
            "check_in_time",
            "check_out_time",
            "status",
            "confidence_score",
            "geolocation",
            "device_info",
            "verification_image_url",
        ]


class PendingReviewSerializer(serializers.ModelSerializer):
    employee_id = serializers.CharField(source="user.employee_id", read_only=True)
    employee_name = serializers.CharField(source="user.username", read_only=True)

    registered_image_url = serializers.SerializerMethodField()
    live_image_url = serializers.SerializerMethodField()

    class Meta:
        model = RemoteAttendance   # ✅ FIXED
        fields = [
            "id",
            "employee_id",
            "employee_name",
            "check_in_time",
            "check_out_time",
            "status",
            "confidence_score",
            "registered_image_url",
            "live_image_url",
        ]

    def get_registered_image_url(self, obj):
        try:
            face = FaceProfile.objects.get(user=obj.user)
            return face.image.url if hasattr(face, "image") and face.image else None
        except FaceProfile.DoesNotExist:
            return None

    def get_live_image_url(self, obj):
        return obj.verification_image_url






