#attendance_ai/view_auth.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers_auth import CustomTokenObtainPairSerializer
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny

class CustomLoginView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer



class LoginAPIView(APIView):
    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")

        user = authenticate(username=username, password=password)

        if not user:
            return Response({"error": "Invalid credentials"}, status=status.HTTP_400_BAD_REQUEST)

        refresh = RefreshToken.for_user(user)

        return Response({
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "username": user.username,
            "employee_id": user.employee_id,  # << FIXED
            "department": user.department,  # optional
            "designation": user.designation, # optional
            "is_admin": user.is_staff or user.is_superuser
        })



class RegisterAPIView(APIView):
    def post(self, request):
        username = request.data.get("username")
        email = request.data.get("email")
        password = request.data.get("password")

        if User.objects.filter(username=username).exists():
            return Response(
                {"error": "Username already exists"},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )

        # Optionally return user info after registration
        return Response({
            "message": "User registered successfully",
            "user": {
                "id": user.id,
                "username": user.username
            }
        }, status=status.HTTP_201_CREATED)
    

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def profile_status(request):
    """
    Returns whether current user's profile has required fields for face registration.
    Endpoint: GET /api/user/profile-status/
    """
    user = request.user
    # Check required fields for "complete profile"
    profile_complete = bool(user.department and user.designation)
    return Response({
        "username": user.username,
        "employee_id": getattr(user, "employee_id", None),
        "department": getattr(user, "department", None),
        "designation": getattr(user, "designation", None),
        "profile_complete": profile_complete
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_profile(request):
    """
    Update department/designation/is_remote_worker for the authenticated user.
    Endpoint: POST /api/user/update-profile/
    Expects JSON body: { department, designation, is_remote_worker }
    """
    user = request.user
    data = request.data

    department = data.get("department")
    designation = data.get("designation")
    is_remote = data.get("is_remote_worker", None)

    # Basic validation
    if not department or not designation:
        return Response({"detail": "department and designation are required."},
                        status=status.HTTP_400_BAD_REQUEST)

    user.department = department
    user.designation = designation

    # If your RegisteredUser model does not have is_remote_worker field, skip
    if hasattr(user, "is_remote_worker"):
        user.is_remote_worker = bool(is_remote)

    user.save()

    return Response({
        "message": "Profile updated",
        "username": user.username,
        "employee_id": getattr(user, "employee_id", None),
        "department": user.department,
        "designation": user.designation
    }, status=status.HTTP_200_OK)

