# attendance_ai/urls.py
from django.urls import path
from .views import FaceRegisterView, AttendanceCheckinView,AttendanceCheckoutView, UserRegisterView
from .userInterface import checkin_page
from .views_auth import profile_status, update_profile
from .views import attendance_history, today_status
from .views_admin import (
   PendingVerificationsView,
   ApproveAttendanceView,
   RejectAttendanceView,
   BatchApproveView,
   AnomalyListView
)

urlpatterns = [
    # User registration (POST)
    path("auth/register/", UserRegisterView.as_view(), name="user_register"),

    # Profile endpoints (NEW)
    path("user/profile-status/", profile_status, name="profile_status"),
    path("user/update-profile/", update_profile, name="update_profile"),

    path("attendance/history/", attendance_history, name="attendance-history"),
    path("attendance/today/", today_status, name="attendance-today"),

    # Face registration (multipart/form-data)
    path("face/register/", FaceRegisterView.as_view(), name="face_register"),

    # Attendance check-in
    path("attendance/checkin/", AttendanceCheckinView.as_view(), name="attendance_checkin"),
    path("attendance/checkout/", AttendanceCheckoutView.as_view(), name="attendance_checkout"),

    path("review/pending/", PendingVerificationsView.as_view()),
    path("review/approve/", ApproveAttendanceView.as_view()),
    path("review/reject/", RejectAttendanceView.as_view()),
    path("review/batch-approve/", BatchApproveView.as_view()),
    path("review/anomalies/", AnomalyListView.as_view()),


    # Optional UI test page
    path("checkin/", checkin_page, name="ui_checkin"),
]


# small debug message to verify module loads (optional)
print(">>> attendance_ai urls loaded")
