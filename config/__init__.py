"""
Config package init — charge Celery au démarrage.
"""

try:
    from .celery import app as celery_app
    __all__ = ("celery_app",)
except ImportError:
    # Celery non disponible sur ce serveur
    pass
