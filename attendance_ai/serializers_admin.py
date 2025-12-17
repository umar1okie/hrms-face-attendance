from rest_framework import serializers
from django.contrib.auth import get_user_model
from attendance_ai.models import FaceEncoding

User = get_user_model()


class AdminStudentSerializer(serializers.ModelSerializer):
    face_registered = serializers.SerializerMethodField()
    face_registered_at = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id",
            "employee_id",
            "username",
            "department",
            "designation",
            "face_registered",
            "face_registered_at",
        )

    def get_face_registered(self, obj):
        return FaceEncoding.objects.filter(user=obj).exists()

    def get_face_registered_at(self, obj):
        encoding = FaceEncoding.objects.filter(user=obj).first()
        return encoding.created_at if encoding else None
