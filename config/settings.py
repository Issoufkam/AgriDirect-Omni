"""
Configuration Django pour AgriDirect-CIV.

Plateforme de circuit court en Côte d'Ivoire reliant
Producteurs, Clients et Livreurs.
"""

import os
from datetime import timedelta
from pathlib import Path

from decouple import Csv, config
import dj_database_url

# ==============================================================================
# CORE SETTINGS
# ==============================================================================

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config("SECRET_KEY")

DEBUG = config("DEBUG", default=False, cast=bool)

ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="localhost", cast=Csv())

# ==============================================================================
# APPLICATION DEFINITION
# ==============================================================================

DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.gis",  # PostGIS
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "rest_framework_simplejwt",
    "corsheaders",
    "django_filters",
    "django_celery_beat",
    "drf_spectacular",
    "phonenumber_field",
    "django_extensions",
]

LOCAL_APPS = [
    "accounts.apps.AccountsConfig",
    "products.apps.ProductsConfig",
    "orders.apps.OrdersConfig",
    "deliveries.apps.DeliveriesConfig",
    "sms_gateway.apps.SmsGatewayConfig",
    "payments.apps.PaymentsConfig",
    "dashboard.apps.DashboardConfig",
    "reviews.apps.ReviewsConfig",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# ==============================================================================
# MIDDLEWARE
# ==============================================================================

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "accounts.middleware.TrackingMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# ==============================================================================
# DATABASE (PostgreSQL + PostGIS)
# ==============================================================================

DATABASES = {
    "default": config(
        "DATABASE_URL",
        default=f"postgis://{config('DB_USER', 'postgres')}:{config('DB_PASSWORD', 'postgres')}@{config('DB_HOST', 'localhost')}:{config('DB_PORT', '5432')}/{config('DB_NAME', 'agridirect_db')}",
        cast=dj_database_url.parse
    )
}
# S'assurer que l'engine est bien postgis pour la prod
DATABASES["default"]["ENGINE"] = "django.contrib.gis.db.backends.postgis"

# ==============================================================================
# AUTHENTICATION
# ==============================================================================

AUTH_USER_MODEL = "accounts.CustomUser"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ==============================================================================
# INTERNATIONALIZATION
# ==============================================================================

LANGUAGE_CODE = "fr-ci"
TIME_ZONE = "Africa/Abidjan"
USE_I18N = True
USE_TZ = True

# ==============================================================================
# STATIC & MEDIA FILES
# ==============================================================================

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# Whitenoise optimization
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

# ==============================================================================
# DEFAULT PRIMARY KEY
# ==============================================================================

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ==============================================================================
# DJANGO REST FRAMEWORK
# ==============================================================================

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "DEFAULT_FILTER_BACKENDS": (
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "100/hour",
        "user": "1000/hour",
    },
}

# ==============================================================================
# SIMPLE JWT
# ==============================================================================

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=2),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
}

# ==============================================================================
# CORS
# ==============================================================================

CORS_ALLOW_ALL_ORIGINS = DEBUG
CORS_ALLOWED_ORIGINS = config(
    "CORS_ALLOWED_ORIGINS",
    default="http://localhost:3000,http://localhost:8080,http://localhost:8081,http://127.0.0.1:8081,https://agridirect-pro-v1.web.app",
    cast=Csv(),
)
CORS_ALLOW_CREDENTIALS = True

# ==============================================================================
# CELERY (Tasks asynchrones)
# ==============================================================================

CELERY_BROKER_URL = config("REDIS_URL", default="redis://localhost:6379/0")
CELERY_RESULT_BACKEND = config("REDIS_URL", default="redis://localhost:6379/0")
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"

# ==============================================================================
# AFRICA'S TALKING SMS GATEWAY
# ==============================================================================

AT_USERNAME = config("AT_USERNAME", default="sandbox")
AT_API_KEY = config("AT_API_KEY", default="")

# ==============================================================================
# DELIVERY / LOGISTIQUE SETTINGS
# ==============================================================================

DELIVERY_BASE_FEE = config("DELIVERY_BASE_FEE", default=500, cast=int)
DELIVERY_PER_KM_FEE = config("DELIVERY_PER_KM_FEE", default=150, cast=int)
MAX_DELIVERY_RADIUS_KM = config("MAX_DELIVERY_RADIUS_KM", default=10, cast=int)

# ==============================================================================
# DRF SPECTACULAR (API Documentation)
# ==============================================================================

SPECTACULAR_SETTINGS = {
    "TITLE": "AgriDirect-CIV API",
    "DESCRIPTION": (
        "API de la plateforme de circuit court en Côte d'Ivoire. "
        "Relie Producteurs (Planteurs, Pêcheurs, Bergers, Bouchers), "
        "Clients et Livreurs."
    ),
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
}

# ==============================================================================
# PHONE NUMBER
# ==============================================================================

PHONENUMBER_DEFAULT_REGION = "CI"  # Côte d'Ivoire
PHONENUMBER_DB_FORMAT = "E164"

# ==============================================================================
# LOGGING
# ==============================================================================

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "[{asctime}] {levelname} {name} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "INFO",
        },
        "sms_gateway": {
            "handlers": ["console"],
            "level": "DEBUG",
        },
        "orders": {
            "handlers": ["console"],
            "level": "DEBUG",
        },
        "deliveries": {
            "handlers": ["console"],
            "level": "DEBUG",
        },
    },
}
