"""
Configuration de développement SANS PostGIS/GDAL.

Utilise SQLite standard avec des champs texte pour simuler
les coordonnées GPS. Idéal pour le développement local
sur Windows sans installer GDAL/PostGIS.

Usage:
    set DJANGO_SETTINGS_MODULE=config.settings_dev
    python manage.py runserver
"""

from .settings import *  # noqa: F401, F403

# Remplacer le moteur GIS par SQLite standard
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",  # noqa: F405
    }
}

# Retirer django.contrib.gis des apps installées
INSTALLED_APPS = [  # noqa: F405
    app for app in INSTALLED_APPS if app != "django.contrib.gis"
]

# Config pour les tests unitaires locaux
CELERY_TASK_ALWAYS_EAGER = True
