#attendance/views_admin.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from rest_framework import status
from .models import RemoteAttendance, AttendanceAnomaly
from django.utils import timezone


class PendingVerificationsView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        items = RemoteAttendance.objects.filter(status="pending").order_by("-check_in_time")

        data = []
        for a in items:
            data.append({
                "id": a.id,
                "employee_id": a.user.employee_id,
                "employee_name": a.user.username,
                "check_in_time": a.check_in_time,
                "confidence_score": a.confidence_score,
                "image_url": a.verification_image_url,
            })

        return Response(data)


# attendance_ai/views_admin.py

class ApproveAttendanceView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request, pk=None):
        notes = request.data.get("notes", "")

        # 1️⃣ Prefer attendance ID from URL
        if pk:
            attendance = RemoteAttendance.objects.filter(
                id=pk,
                status="pending"
            ).first()
        else:
            # 2️⃣ Fallback: approve by employee_id
            employee_id = request.data.get("employee_id")
            if not employee_id:
                return Response(
                    {"error": "attendance id (pk) or employee_id required"},
                    status=400
                )

            attendance = RemoteAttendance.objects.filter(
                user__employee_id=employee_id,
                status="pending"
            ).order_by("-check_in_time").first()

        if not attendance:
            return Response(
                {"error": "No pending attendance found"},
                status=404
            )

        attendance.status = "approved"
        attendance.review_notes = notes
        attendance.reviewed_by = request.user
        attendance.reviewed_at = timezone.now()
        attendance.save()

        return Response({
            "status": "approved",
            "attendance_id": attendance.id,
            "employee_id": attendance.user.employee_id
        })


    

class RejectAttendanceView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request, pk=None):
        notes = request.data.get("notes", "")

        if pk:
            attendance = RemoteAttendance.objects.filter(
                id=pk,
                status="pending"
            ).first()
        else:
            employee_id = request.data.get("employee_id")
            if not employee_id:
                return Response(
                    {"error": "attendance id (pk) or employee_id required"},
                    status=400
                )

            attendance = RemoteAttendance.objects.filter(
                user__employee_id=employee_id,
                status="pending"
            ).order_by("-check_in_time").first()

        if not attendance:
            return Response(
                {"error": "No pending attendance found"},
                status=404
            )

        attendance.status = "rejected"
        attendance.review_notes = notes
        attendance.reviewed_by = request.user
        attendance.reviewed_at = timezone.now()
        attendance.save()

        return Response({
            "status": "rejected",
            "attendance_id": attendance.id,
            "employee_id": attendance.user.employee_id
        })




class BatchApproveView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request):
        employee_ids = request.data.get("employee_ids")

        if not employee_ids or not isinstance(employee_ids, list):
            return Response(
                {"error": "employee_ids must be a non-empty list"},
                status=400
            )

        approved = []
        skipped = []

        for emp_id in employee_ids:
            attendance = RemoteAttendance.objects.filter(
                user__employee_id=emp_id,
                status="pending"
            ).order_by("-check_in_time").first()

            if not attendance:
                skipped.append(emp_id)
                continue

            attendance.status = "approved"
            attendance.reviewed_by = request.user
            attendance.reviewed_at = timezone.now()
            attendance.save()

            approved.append(emp_id)

        return Response({
            "status": "batch_approved",
            "approved_employee_ids": approved,
            "skipped_employee_ids": skipped,
            "approved_count": len(approved)
        })



class AnomalyListView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        anomalies = AttendanceAnomaly.objects.select_related(
            "attendance", "attendance__user"
        ).order_by("-detected_at")

        data = [{
            "id": a.id,
            "attendance_id": a.attendance.id if a.attendance else None,
            "employee_id": a.attendance.user.employee_id if a.attendance else None,
            "employee_name": a.attendance.user.username if a.attendance else None,
            "type": a.anomaly_type,
            "severity": a.severity,
            "description": a.description,
            "detected_at": a.detected_at,
        } for a in anomalies]

        return Response(data)
    



