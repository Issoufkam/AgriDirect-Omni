"""
Utilitaires géospatiaux compatibles PostGIS et SQLite.

En production avec PostGIS : Utilise les vrais PointField de GeoDjango.
En développement sans PostGIS : Utilise des champs Float (lat/lng séparés).

Ce module fournit un wrapper transparent pour la géolocalisation.
"""

import math

from django.conf import settings
from django.db import models

# Détecter si PostGIS/GeoDjango est disponible
HAS_GIS = "django.contrib.gis" in settings.INSTALLED_APPS

if HAS_GIS:
    from django.contrib.gis.db import models as gis_models
    from django.contrib.gis.geos import Point
    from django.contrib.gis.measure import D


def get_location_fields(field_name: str, verbose_name: str = "localisation", **kwargs):
    """
    Retourne les champs de modèle appropriés pour stocker une localisation.

    Avec PostGIS : retourne un PointField.
    Sans PostGIS : retourne deux FloatField (latitude, longitude).

    Args:
        field_name: Nom de base du champ.
        verbose_name: Label du champ.
        **kwargs: Arguments supplémentaires (null, blank, etc.).

    Returns:
        Dictionnaire {nom_champ: field_instance}.
    """
    if HAS_GIS:
        return {
            field_name: gis_models.PointField(
                verbose_name,
                srid=4326,
                **kwargs,
            )
        }
    else:
        null = kwargs.get("null", False)
        blank = kwargs.get("blank", False)
        return {
            f"{field_name}_lat": models.FloatField(
                f"{verbose_name} (latitude)",
                null=null,
                blank=blank,
                default=None if null else 0.0,
            ),
            f"{field_name}_lng": models.FloatField(
                f"{verbose_name} (longitude)",
                null=null,
                blank=blank,
                default=None if null else 0.0,
            ),
        }


def make_point(longitude: float, latitude: float):
    """
    Crée un objet point compatible avec le backend actif.

    Args:
        longitude: Longitude en degrés.
        latitude: Latitude en degrés.

    Returns:
        Point (PostGIS) ou tuple (lat, lng).
    """
    if HAS_GIS:
        return Point(longitude, latitude, srid=4326)
    return (latitude, longitude)


def get_lat_lng(obj, field_name: str) -> tuple:
    """
    Extrait la latitude et longitude d'un objet modèle.

    Args:
        obj: Instance du modèle.
        field_name: Nom du champ de localisation.

    Returns:
        Tuple (latitude, longitude) ou (None, None).
    """
    if HAS_GIS:
        point = getattr(obj, field_name, None)
        if point:
            return (point.y, point.x)
        return (None, None)
    else:
        lat = getattr(obj, f"{field_name}_lat", None)
        lng = getattr(obj, f"{field_name}_lng", None)
        return (lat, lng)


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calcule la distance en kilomètres entre deux points GPS
    en utilisant la formule de Haversine.

    Args:
        lat1: Latitude du point 1 en degrés.
        lon1: Longitude du point 1 en degrés.
        lat2: Latitude du point 2 en degrés.
        lon2: Longitude du point 2 en degrés.

    Returns:
        Distance en kilomètres.
    """
    R = 6371  # Rayon de la Terre en km

    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c
