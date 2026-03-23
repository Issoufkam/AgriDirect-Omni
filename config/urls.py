"""
URLs racine du projet AgriDirect-CIV.

Centralise toutes les routes API et la documentation Swagger.
"""

from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from django.views.generic import RedirectView

urlpatterns = [
    # ── Admin ──
    path("admin/", admin.site.urls),
    # ── Authentication JWT ──
    path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    # ── Apps ──
    path("api/", include("accounts.urls")),
    path("api/", include("products.urls")),
    path("api/", include("orders.urls")),
    path("api/", include("deliveries.urls")),
    path("api/", include("sms_gateway.urls")),
    path("api/payments/", include("payments.urls")),
    path("api/", include("reviews.urls")),
    path("", include("dashboard.urls")),
    path("", include("products.urls")),
    path("", include("deliveries.urls")),
    path("", include("orders.urls")),
    path("", include("accounts.urls")),
    
    # ── Page d'accueil ──
    path("", RedirectView.as_view(url='/marketplace/'), name='root-redirect'),
    
    # ── API Documentation ──
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path(
        "api/redoc/",
        SpectacularRedocView.as_view(url_name="schema"),
        name="redoc",
    ),
]
