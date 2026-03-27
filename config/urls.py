"""
URLs racine du projet AgriDirect-CIV.

Centralise toutes les routes API et la documentation Swagger.
"""

from django.contrib import admin
from django.urls import include, path
from products.views import MarketplaceUIView
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

urlpatterns = [
    # ── Admin ──
    path("admin/", admin.site.urls),

    # ── Accueil : Marketplace (En direct pour éviter le 302 et corriger Render) ──
    path("", MarketplaceUIView.as_view(), name='marketplace_ui_root'),

    # ── Application Principale (Inclus les routes UI ET API de chaque module) ──
    # Note: On inclut à la racine "". C'est chaque `urls.py` d'app qui gère
    # le fait de préfixer par "api/" ses propres routes API.
    path("", include("accounts.urls")),
    path("", include("products.urls")),
    path("", include("orders.urls")),
    path("", include("deliveries.urls")),
    path("", include("dashboard.urls")),

    # ── Autres Services API (REST uniquement, donc on peut préfixer par api/) ──
    path("api/payments/", include("payments.urls")),
    path("api/sms/", include("sms_gateway.urls")),
    path("api/reviews/", include("reviews.urls")),
    
    # ── API Documentation ──
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]

# ── Service des fichiers MEDIA (Uniquement en développement) ──
from django.conf import settings
from django.conf.urls.static import static

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
