# attendance_ai/middleware.py
import time
from django.core.cache import cache
from django.http import JsonResponse
from jwt import decode as jwt_decode
from django.conf import settings
from django.contrib.auth import get_user_model
from channels.middleware import BaseMiddleware
from channels.db import database_sync_to_async
from urllib.parse import parse_qs


User = get_user_model()

@database_sync_to_async
def get_user_from_token(token):
    try:
        payload = jwt_decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        return User.objects.get(id=payload["user_id"])
    except Exception:
        return None


class JWTAuthMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        query_string = parse_qs(scope["query_string"].decode())
        token = query_string.get("token")

        if token:
            scope["user"] = await get_user_from_token(token[0])
        else:
            scope["user"] = None

        return await super().__call__(scope, receive, send)


class RateLimitMiddleware:
    """
    Very simple rate limit:
    - Keyed by IP or user id
    - Allows N requests per window seconds
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.WINDOW = 60   # seconds
        self.LIMIT = 10    # requests per window

    def __call__(self, request):
        # apply only to attendance checkin endpoint
        path = request.path
        if path.startswith("/api/attendance/checkin/"):
            ip = request.META.get("REMOTE_ADDR", "anon")
            key = f"rl:{ip}"
            data = cache.get(key) or {"count": 0, "start": time.time()}
            now = time.time()
            if now - data["start"] > self.WINDOW:
                data = {"count": 0, "start": now}
            data["count"] += 1
            cache.set(key, data, timeout=self.WINDOW + 5)
            if data["count"] > self.LIMIT:
                return JsonResponse({"detail": "Rate limit exceeded"}, status=429)
        return self.get_response(request)


