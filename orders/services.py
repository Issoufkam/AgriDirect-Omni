"""
Services métier pour l'application Orders.

Contient la logique de création de commande avec calcul
automatique des prix et frais de livraison.
"""

import logging
from decimal import Decimal

from django.conf import settings
from django.db import transaction

from products.services import haversine_distance
from products.models import Stock
from sms_gateway.services import send_sms
import random

from .models import Order

logger = logging.getLogger(__name__)


def calculate_delivery_fee(distance_km: float) -> Decimal:
    """
    Calcule les frais de livraison selon la distance réelle et l'état des routes (simulé).

    Args:
        distance_km: Distance en kilomètres.

    Returns:
        Frais de livraison en FCFA.
    """
    base_fee = settings.DELIVERY_BASE_FEE
    per_km_fee = settings.DELIVERY_PER_KM_FEE
    
    # ── Détermination de l'état des routes (Déterministe pour la prévisibilité) ──
    # Simulation: Si la distance est grande (> 5km), on assume 20% de pistes rurales.
    road_condition_multiplier = 1.0
    if distance_km > 5:
        road_condition_multiplier = 1.20
    
    fee = (base_fee + (Decimal(str(distance_km)) * per_km_fee)) * Decimal(str(road_condition_multiplier))
    return Decimal(str(round(fee)))


@transaction.atomic
def create_order(
    client,
    stock_id: int,
    quantity: float,
    delivery_address: str,
    client_lat: float,
    client_lng: float,
) -> Order:
    """
    Crée une commande avec calcul automatique des prix.

    Étapes :
        1. Vérifie le stock disponible.
        2. Applique le prix national (protection des prix).
        3. Calcule la distance producteur-client (Haversine).
        4. Calcule les frais de livraison.
        5. Crée la commande.
        6. Décrémente le stock du producteur.

    Args:
        client: Instance de l'utilisateur client.
        stock_id: ID du stock à commander.
        quantity: Quantité souhaitée.
        delivery_address: Adresse de livraison textuelle.
        client_lat: Latitude du client.
        client_lng: Longitude du client.

    Returns:
        Instance de la commande créée.

    Raises:
        ValueError: Stock insuffisant ou stock introuvable.
    """
    # ── 1. Vérification du stock ──
    try:
        stock = Stock.objects.select_for_update().get(pk=stock_id)
    except Stock.DoesNotExist:
        raise ValueError(f"Stock #{stock_id} introuvable.")

    quantity_decimal = Decimal(str(quantity))

    if stock.available_quantity < quantity_decimal:
        raise ValueError(
            f"Stock insuffisant. Disponible (non réservé): {stock.available_quantity} "
            f"{stock.product.get_unit_display()}, demandé: {quantity_decimal}."
        )

    # ── 2. Prix national imposé (Protection des Prix) ──
    unit_price = stock.product.national_price
    total_product = unit_price * quantity_decimal

    # ── 3. Calcul de la distance ──
    distance_km = haversine_distance(
        client_lat,
        client_lng,
        stock.location_lat,
        stock.location_lng,
    )

    # ── 4. Frais de livraison ──
    delivery_fee = calculate_delivery_fee(distance_km)

    # ── 5. Montant total ──
    total_amount = total_product + delivery_fee

    # ── 6. Création de la commande ──
    order = Order.objects.create(
        client=client,
        stock=stock,
        quantity=quantity_decimal,
        unit_price=unit_price,
        total_product_amount=total_product,
        delivery_fee=delivery_fee,
        total_amount=total_amount,
        delivery_address=delivery_address,
        client_location_lat=client_lat,
        client_location_lng=client_lng,
        status=Order.Status.PENDING,
        payment_status=Order.PaymentStatus.UNPAID,
    )

    # ── 7. Réservation du stock (Bloqué temporairement) ──
    stock.reserved_quantity += quantity_decimal
    stock.save(update_fields=["reserved_quantity", "updated_at"])

    # ── 8. ALERTE STOCK BAS (Relance SMS) ──
    if stock.remaining_quantity <= 10:
        alert_msg = (
            f"AgriDirect ALERTE: Votre stock de {stock.product.name} est bas! "
            f"Il ne reste que {stock.remaining_quantity} {stock.product.get_unit_display()}. "
            "Pensez à le réapprovisionner pour ne pas rater de ventes."
        )
        send_sms(str(stock.producer.phone_number), alert_msg)
        logger.info(f"Alerte stock bas envoyée au producteur {stock.producer.get_full_name()}")

    logger.info(
        "Commande #%d créée: %s x %s %s = %s FCFA + %s FCFA livraison "
        "(distance: %.2f km). Total: %s FCFA",
        order.pk,
        quantity_decimal,
        stock.product.name,
        stock.product.get_unit_display(),
        total_product,
        delivery_fee,
        distance_km,
        total_amount,
    )

    return order


def cancel_order(order: Order) -> Order:
    """
    Annule une commande et restitue le stock.

    Ne peut annuler que les commandes en status PENDING ou ASSIGNED.

    Args:
        order: Instance de la commande à annuler.

    Returns:
        Commande mise à jour.

    Raises:
        ValueError: Si la commande ne peut pas être annulée.
    """
    if order.status not in (Order.Status.PENDING, Order.Status.ASSIGNED):
        raise ValueError(
            f"Impossible d'annuler une commande au statut '{order.get_status_display()}'."
        )

    with transaction.atomic():
        # Libérer la réservation
        stock = Stock.objects.select_for_update().get(pk=order.stock_id)
        stock.reserved_quantity = max(0, stock.reserved_quantity - order.quantity)
        stock.save(update_fields=["reserved_quantity", "updated_at"])

        # Mettre à jour le statut
        order.status = Order.Status.CANCELLED
        if order.payment_status == Order.PaymentStatus.ESCROWED:
            order.payment_status = Order.PaymentStatus.REFUNDED
        order.save(update_fields=["status", "payment_status", "updated_at"])

    logger.info("Commande #%d annulée. Stock restitué.", order.pk)
    return order
