"""
Services métier pour l'application Deliveries.

Contient le moteur de dispatch logistique et la validation OTP.
"""

import logging
from decimal import Decimal

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from accounts.models import CustomUser
from orders.models import Order
from products.services import haversine_distance

from .models import Delivery

logger = logging.getLogger(__name__)


def find_available_drivers(order: Order, radius_km: float = None) -> list:
    """
    Recherche les livreurs disponibles autour du producteur.

    Critères :
        1. Livreur actif (is_active_driver=True).
        2. Dans un rayon de `radius_km` autour du producteur.
        3. Si le produit nécessite réfrigération, seuls les livreurs
           avec has_refrigeration=True sont considérés.

    Args:
        order: Commande pour laquelle on cherche un livreur.
        radius_km: Rayon de recherche en km (défaut: MAX_DELIVERY_RADIUS_KM).

    Returns:
        Liste de tuples (driver, distance_km) triés par distance croissante.
    """
    if radius_km is None:
        radius_km = settings.MAX_DELIVERY_RADIUS_KM

    stock = order.stock
    producer_lat = stock.location_lat
    producer_lng = stock.location_lng

    if producer_lat is None or producer_lng is None:
        logger.warning(
            "Commande #%d: pas de localisation pour le producteur.", order.pk
        )
        return []

    # Filtrer les livreurs actifs avec localisation
    drivers = CustomUser.objects.filter(
        role=CustomUser.Role.LIVREUR,
        is_active_driver=True,
        current_location_lat__isnull=False,
        current_location_lng__isnull=False,
    )

    # Si le produit nécessite réfrigération
    if stock.needs_refrigeration:
        drivers = drivers.filter(has_refrigeration=True)
        logger.info(
            "Commande #%d: produit frais — filtrage livreurs avec réfrigération.",
            order.pk,
        )

    # Calculer les distances et filtrer par rayon
    results = []
    for driver in drivers:
        distance = haversine_distance(
            producer_lat,
            producer_lng,
            driver.current_location_lat,
            driver.current_location_lng,
        )

        if distance <= radius_km:
            results.append((driver, round(distance, 2)))

    results.sort(key=lambda x: x[1])

    logger.info(
        "Commande #%d: %d livreurs trouvés dans un rayon de %d km.",
        order.pk,
        len(results),
        radius_km,
    )

    return results


@transaction.atomic
def assign_delivery(order: Order, driver: CustomUser) -> Delivery:
    """
    Assigne un livreur à une commande et crée la livraison.

    Étapes :
        1. Vérifie que la commande est en PENDING.
        2. Crée une instance Delivery avec OTP auto-généré.
        3. Met à jour le statut de la commande en ASSIGNED.

    Args:
        order: Commande à assigner.
        driver: Livreur assigné.

    Returns:
        Instance de la livraison créée.

    Raises:
        ValueError: Si la commande n'est pas en PENDING ou le livreur invalide.
    """
    if order.status != Order.Status.PENDING:
        raise ValueError(
            f"Commande #{order.pk} n'est pas en attente "
            f"(statut actuel: {order.get_status_display()})."
        )

    if not driver.is_livreur:
        raise ValueError(f"{driver} n'est pas un livreur.")

    # Créer la livraison
    delivery = Delivery.objects.create(
        order=order,
        driver=driver,
        delivery_fee=order.delivery_fee,
    )

    # Mettre à jour le statut de la commande
    order.status = Order.Status.ASSIGNED
    order.save(update_fields=["status", "updated_at"])

    logger.info(
        "Livraison #%d créée — Commande #%d assignée à %s (OTP: %s).",
        delivery.pk,
        order.pk,
        driver.get_full_name(),
        delivery.otp_code,
    )

    return delivery


@transaction.atomic
def update_delivery_status(
    delivery: Delivery,
    new_status: str,
    otp_code: str = None,
) -> Delivery:
    """
    Met à jour le statut d'une livraison.

    Transitions valides :
        ASSIGNED → EN_ROUTE_PICKUP
        EN_ROUTE_PICKUP → PICKED_UP (enregistre pickup_time)
        PICKED_UP → EN_ROUTE_DELIVERY
        EN_ROUTE_DELIVERY → DELIVERED (nécessite OTP + enregistre delivery_time)

    Pour finaliser la livraison (DELIVERED), le livreur doit fournir
    le code OTP reçu du client. Cela déclenche la libération du séquestre.

    Args:
        delivery: Instance de la livraison.
        new_status: Nouveau statut souhaité.
        otp_code: Code OTP (obligatoire pour passer à DELIVERED).

    Returns:
        Livraison mise à jour.

    Raises:
        ValueError: Transition invalide ou OTP incorrect.
    """
    valid_transitions = {
        Delivery.Status.ASSIGNED: [Delivery.Status.EN_ROUTE_PICKUP],
        Delivery.Status.EN_ROUTE_PICKUP: [Delivery.Status.PICKED_UP],
        Delivery.Status.PICKED_UP: [Delivery.Status.EN_ROUTE_DELIVERY],
        Delivery.Status.EN_ROUTE_DELIVERY: [Delivery.Status.DELIVERED],
    }

    allowed = valid_transitions.get(delivery.status, [])
    if new_status not in allowed:
        raise ValueError(
            f"Transition invalide: {delivery.get_status_display()} → {new_status}. "
            f"Transitions autorisées: {[s.label for s in allowed]}."
        )

    now = timezone.now()

    # Gestion des transitions spéciales
    if new_status == Delivery.Status.PICKED_UP:
        delivery.pickup_time = now
        # Mettre à jour la commande
        delivery.order.status = Order.Status.PICKED_UP
        delivery.order.save(update_fields=["status", "updated_at"])

    elif new_status == Delivery.Status.DELIVERED:
        # Validation OTP obligatoire
        if not otp_code:
            raise ValueError("Le code OTP est obligatoire pour finaliser la livraison.")

        if otp_code != delivery.otp_code:
            raise ValueError("Code OTP incorrect.")

        delivery.delivery_time = now

        # Libération du séquestre via le service de paiement
        order = delivery.order
        order.status = Order.Status.DELIVERED
        order.save(update_fields=["status", "updated_at"])
        
        from payments.services import MobileMoneyService
        if order.payment_status == Order.PaymentStatus.ESCROWED:
            MobileMoneyService.release_escrow(order)
        elif order.payment_status != Order.PaymentStatus.RELEASED:
            order.payment_status = Order.PaymentStatus.RELEASED
            order.save(update_fields=["payment_status"])

        logger.info(
            "Livraison #%d terminée — OTP validé — Séquestre libéré pour "
            "commande #%d (%s FCFA).",
            delivery.pk,
            order.pk,
            order.total_amount,
        )

    delivery.status = new_status
    delivery.save()

    logger.info(
        "Livraison #%d: statut mis à jour → %s.",
        delivery.pk,
        delivery.get_status_display(),
    )

    return delivery


def auto_dispatch_order(order: Order) -> Delivery | None:
    """
    Dispatch automatique: cherche le livreur le plus proche et
    assigne la commande.

    Args:
        order: Commande à dispatcher.

    Returns:
        Delivery si un livreur a été trouvé, None sinon.
    """
    available_drivers = find_available_drivers(order)

    if not available_drivers:
        logger.warning(
            "Commande #%d: aucun livreur disponible dans le rayon.",
            order.pk,
        )
        return None

    # Prendre le livreur le plus proche
    closest_driver, distance = available_drivers[0]

    logger.info(
        "Commande #%d: auto-dispatch vers %s (%.2f km).",
        order.pk,
        closest_driver.get_full_name(),
        distance,
    )

    return assign_delivery(order, closest_driver)
