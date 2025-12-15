# attendance_ai/utils/audit.py
from attendance_ai.models import AuditLog
from functools import wraps

def audit_action(action_name):
    def decorator(func):
        @wraps(func)
        def wrapper(view_self, request, *args, **kwargs):
            response = func(view_self, request, *args, **kwargs)
            try:
                # best effort - create a log entry
                AuditLog.objects.create(
                    actor=request.user if getattr(request, "user", None) and request.user.is_authenticated else None,
                    action=action_name,
                    target_repr=getattr(response, "data", {}) or "",
                    extra={"path": request.path},
                    ip_address=request.META.get("REMOTE_ADDR")
                )
            except Exception:
                # do not block main flow if logging fails
                pass
            return response
        return wrapper
    return decorator
