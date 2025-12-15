# attendance_ai/admin.py

from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.auth import get_user_model

from .models import (
    RegisteredUser,
    FaceProfile,
    RemoteAttendance,
    AttendanceAnomaly,
    AuditLog,
)

User = get_user_model()


# ---------------------------------------------------------
# REGISTERED USER ADMIN (MAIN USER)
# ---------------------------------------------------------
@admin.register(RegisteredUser)
class RegisteredUserAdmin(DjangoUserAdmin):
    list_display = (
        "username",
        "email",
        "employee_id",
        "department",
        "designation",
        "is_remote_worker",
        "is_active",
        "is_staff",
        "is_superuser"
    )

    search_fields = (
        "username",
        "email",
        "employee_id",
        "first_name",
        "last_name",
    )

    fieldsets = DjangoUserAdmin.fieldsets + (
        ("Employee Information", {
            "fields": (
                "employee_id",
                "department",
                "designation",
            )
        }),
    )


# ---------------------------------------------------------
# FACE PROFILE ADMIN
# ---------------------------------------------------------
@admin.register(FaceProfile)
class FaceProfileAdmin(admin.ModelAdmin):
    list_display = (
        "user_link",
        "encoding_version",
        "is_active",
        "consent_given",
        "created_at",
    )

    list_filter = ("is_active", "encoding_version", "consent_given")

    search_fields = (
        "user__username",
        "user__email",
        "user__employee_id",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
        "face_encoding_preview",
    )

    def user_link(self, obj):
        url = reverse("admin:attendance_ai_registereduser_change", args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.username)

    user_link.short_description = "User"

    def face_encoding_preview(self, obj):
        if not obj.face_encoding:
            return "-"
        return format_html("<code>{}...</code>", str(obj.face_encoding)[:200])

    face_encoding_preview.short_description = "Encoding Preview"


# ---------------------------------------------------------
# REMOTE ATTENDANCE ADMIN
# ---------------------------------------------------------
@admin.register(RemoteAttendance)
class RemoteAttendanceAdmin(admin.ModelAdmin):
    list_display = (
        "user_link",
        "check_in_time",
        "check_out_time",
        "status",
        "confidence_badge",
        "verification_image_small",
    )

    list_filter = ("status", "check_in_time","check_out_time")
    search_fields = ("user__username", "user__employee_id")

    readonly_fields = ("verification_image_small",)

    def user_link(self, obj):
        url = reverse("admin:attendance_ai_registereduser_change", args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.username)

    user_link.short_description = "User"

    def verification_image_small(self, obj):
        if obj.verification_image_url:
            return format_html(
                '<img src="{}" style="max-height:80px;border-radius:4px;" />',
                obj.verification_image_url
            )
        return "-"

    verification_image_small.short_description = "Verification Image"

    def confidence_badge(self, obj):
        score = obj.confidence_score or 0
        color = "red" if score < 0.5 else "orange" if score < 0.75 else "green"

        percent = f"{score * 100:.1f}%"  # manually create percent string

        return format_html(
            '<span style="padding:4px 8px;border-radius:4px;background:{};color:white;">'
            '{}'
            '</span>',
            color,
            percent
    )

    confidence_badge.short_description = "Confidence"


# ---------------------------------------------------------
# ATTENDANCE ANOMALY
# ---------------------------------------------------------
@admin.register(AttendanceAnomaly)
class AttendanceAnomalyAdmin(admin.ModelAdmin):
    list_display = (
        "attendance",
        "anomaly_type",
        "severity",
        "detected_at",
        "resolved",
    )

    list_filter = (
        "anomaly_type",
        "severity",
        "resolved",
    )

    search_fields = (
        "attendance__user__username",
        "attendance__user__employee_id",
    )


# ---------------------------------------------------------
# AUDIT LOG ADMIN
# ---------------------------------------------------------
@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = (
        "timestamp",
        "actor_link",
        "action",
        "target_repr",
        "ip_address",
        "extra_short",
    )

    list_filter = ("action", "timestamp")
    search_fields = ("actor__username", "action", "target_repr", "ip_address")

    def actor_link(self, obj):
        if not obj.actor:
            return "-"
        url = reverse("admin:attendance_ai_registereduser_change", args=[obj.actor.id])
        return format_html('<a href="{}">{}</a>', url, obj.actor.username)

    actor_link.short_description = "Actor"

    def extra_short(self, obj):
        if not obj.extra:
            return "-"
        text = str(obj.extra)
        return text if len(text) < 80 else text[:80] + "..."

    extra_short.short_description = "Extra"
