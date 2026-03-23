"""
Services métier pour l'application Products.

Contient la logique de la marketplace et la recherche géolocalisée.
"""

import logging
import math
from decimal import Decimal

from django.db.models import F
from .models import Stock

logger = logging.getLogger(__name__)


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


def get_marketplace_stocks(
    latitude: float = None,
    longitude: float = None,
    radius_km: float = None,
    category: str = None,
    product_name: str = None,
):
    """
    Récupère les stocks disponibles sur la marketplace.

    Filtre par proximité géographique, catégorie et nom de produit.
    Les résultats sont triés par distance si la position du client est fournie.

    Args:
        latitude: Latitude du client.
        longitude: Longitude du client.
        radius_km: Rayon de recherche en km (défaut: pas de limite).
        category: Filtre par catégorie (VIVRIER, CARNE, HALIEUTIQUE, ELEVAGE).
        product_name: Filtre par nom de produit (recherche partielle).

    Returns:
        Liste de dictionnaires avec les infos de chaque stock disponible,
        triés par distance si la position est fournie.
    """
    queryset = Stock.objects.filter(
        remaining_quantity__gt=0,
        product__is_active=True,
    ).select_related("product", "producer")

    # ── Filtre par catégorie ──
    if category:
        queryset = queryset.filter(product__category=category.upper())

    # ── Filtre par nom de produit ──
    if product_name:
        queryset = queryset.filter(product__name__icontains=product_name)

    results = []
    for stock in queryset:
        item = {
            "id": stock.id,
            "product": {
                "name": stock.product.name,
                "category_display": stock.product.get_category_display(),
                "unit": stock.product.get_unit_display(),
                "original_price": stock.product.national_price,
                "unit_price": stock.unit_price,
                "image": stock.product.image.url if stock.product.image else None,
            },
            "remaining_quantity": stock.remaining_quantity,
            "producer": {
                "full_name": stock.producer.get_full_name(),
                "phone": str(stock.producer.phone_number),
                "average_rating": stock.producer.average_rating,
            },
            "needs_refrigeration": stock.needs_refrigeration,
            "location_lat": stock.location_lat,
            "location_lng": stock.location_lng,
            "distance_km": None,
        }

        # Calcul de la distance Haversine
        if latitude is not None and longitude is not None:
            distance = haversine_distance(
                latitude, longitude, stock.location_lat, stock.location_lng
            )
            item["distance_km"] = round(distance, 2)

            # Filtre par rayon
            if radius_km and distance > radius_km:
                continue

        results.append(item)

    # Tri par distance si position fournie
    if latitude is not None and longitude is not None:
        results.sort(key=lambda x: x["distance_km"] or float("inf"))

    logger.info(
        "Marketplace: %d stocks trouvés (lat=%s, lng=%s, rayon=%s km)",
        len(results),
        latitude,
        longitude,
        radius_km,
    )

    return results


def apply_dynamic_pricing_scan():
    """
    Moteur de mitigation du gaspillage (Anti-Waste Engine).
    
    Parcourt tous les stocks actifs et ajuste la 'dynamic_discount'
    selon des règles métier strictes pour favoriser l'écoulement rapide.
    
    Règles :
        1. Aliments périssables (réfrigérés) de plus de 48h -> 20% de remise.
        2. Surplus de stock ( > 500 unités) -> 10% de remise.
        3. Produits "vieux" ( > 7 jours) non périssables -> 15% de remise.
    """
    from django.utils import timezone
    from datetime import timedelta
    
    now = timezone.now()
    stocks = Stock.objects.filter(remaining_quantity__gt=0).select_related('product')
    
    count_updated = 0
    
    for s in stocks:
        old_discount = s.dynamic_discount
        new_discount = Decimal("0.00")
        
        age_days = (now - s.created_at).days
        
        # Règle 1 : Périssables urgents
        if s.needs_refrigeration or s.product.needs_refrigeration:
            if age_days >= 2:
                new_discount = Decimal("0.20")
        
        # Règle 2 : Surplus (si pas déjà en grosse remise)
        if new_discount == 0 and s.remaining_quantity > 500:
            new_discount = Decimal("0.10")
            
        # Règle 3 : Ancienneté générale
        if age_days >= 7 and new_discount < Decimal("0.15"):
            new_discount = Decimal("0.15")
            
        if new_discount != old_discount:
            s.dynamic_discount = new_discount
            s.save(update_fields=['dynamic_discount', 'updated_at'])
            count_updated += 1
            
    logger.info(f"Dynamic Pricing Scan: {count_updated} stocks mis à jour.")
    return count_updated
