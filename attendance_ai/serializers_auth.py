# attendance_ai/serializer_auth.py
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)

        user = self.user

        data["username"] = user.username
        data["employee_id"] = user.employee_id
        data["department"] = user.department
        data["designation"] = user.designation

        # =========================
        # ✅ ADD THESE LINES ONLY
        # =========================
        data["is_admin"] = user.is_staff or user.is_superuser

        return data
