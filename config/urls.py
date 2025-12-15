# config/urls.py
from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.conf import settings
from django.conf.urls.static import static
from attendance_ai.views_auth import CustomLoginView, RegisterAPIView


urlpatterns = [
    path("admin/", admin.site.urls),

    # JWT auth endpoints (token obtain & refresh)
    path("api/auth/login/", CustomLoginView.as_view(), name="custom_token_obtain_pair"),
    path("api/auth/register/", RegisterAPIView.as_view(), name="custom_register"),
    # path("api/auth/login/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),

    # Include attendance app API under /api/
    path("api/", include("attendance_ai.urls")),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
