"""
Tâches Celery pour l'application SMS Gateway.

Traitement asynchrone des SMS et notifications.
"""

import logging

from celery import shared_task

from .services import SMSParseError, process_stock_sms, send_sms

logger = logging.getLogger("sms_gateway")


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    name="sms_gateway.process_sms",
)
def process_sms_task(self, phone_number: str, raw_text: str, latitude=None, longitude=None):
    """
    Tâche asynchrone pour traiter un SMS de stock.

    Utilisée quand le webhook reçoit un SMS et délègue le traitement
    à Celery pour ne pas bloquer la réponse HTTP.

    Args:
        phone_number: Numéro de l'expéditeur.
        raw_text: Texte brut du SMS.
        latitude: Latitude GPS (optionnel).
        longitude: Longitude GPS (optionnel).
    """
    try:
        result = process_stock_sms(
            phone_number=phone_number,
            raw_text=raw_text,
            latitude=latitude,
            longitude=longitude,
        )
        logger.info("Tâche SMS terminée pour %s: %s", phone_number, result)
        return result

    except SMSParseError as e:
        logger.warning("Erreur parsing SMS (tâche): %s", e)
        # Envoyer un SMS d'erreur au producteur
        send_sms(
            phone_number,
            f"AgriDirect: Erreur dans votre SMS. {str(e)}"
        )
        return {"success": False, "error": str(e)}

    except Exception as exc:
        logger.exception("Erreur inattendue dans tâche SMS")
        self.retry(exc=exc)


@shared_task(name="sms_gateway.send_notification_sms")
def send_notification_sms_task(phone_number: str, message: str):
    """
    Tâche asynchrone pour envoyer un SMS de notification.

    Utilisée pour les notifications de commande, livraison, etc.

    Args:
        phone_number: Numéro du destinataire.
        message: Contenu du SMS.
    """
    success = send_sms(phone_number, message)
    if success:
        logger.info("Notification SMS envoyée à %s", phone_number)
    else:
        logger.error("Échec envoi notification SMS à %s", phone_number)
    return success


@shared_task(name="sms_gateway.notify_order_created")
def notify_order_created_task(order_id: int):
    """
    Notifie le producteur et le client qu'une commande a été créée.

    Args:
        order_id: ID de la commande.
    """
    from orders.models import Order

    try:
        order = Order.objects.select_related(
            "client", "stock__producer", "stock__product"
        ).get(pk=order_id)
    except Order.DoesNotExist:
        logger.error("Commande #%d introuvable pour notification.", order_id)
        return

    # Notification au producteur
    producer_msg = (
        f"AgriDirect: Nouvelle commande #{order.pk}! "
        f"{order.quantity} {order.product.get_unit_display()} de {order.product.name} "
        f"par {order.client.get_full_name()}. "
        f"Montant: {order.total_product_amount} FCFA."
    )
    send_sms(order.stock.producer.phone_number, producer_msg)

    # Notification au client
    client_msg = (
        f"AgriDirect: Commande #{order.pk} confirmée! "
        f"{order.quantity} {order.product.get_unit_display()} de {order.product.name}. "
        f"Total: {order.total_amount} FCFA (dont {order.delivery_fee} FCFA livraison). "
        f"Un livreur sera bientôt assigné."
    )
    send_sms(order.client.phone_number, client_msg)

    logger.info("Notifications envoyées pour commande #%d.", order.pk)


@shared_task(name="sms_gateway.notify_delivery_assigned")
def notify_delivery_assigned_task(delivery_id: int):
    """
    Notifie le client que sa livraison est en cours et lui envoie le code OTP.

    Args:
        delivery_id: ID de la livraison.
    """
    from deliveries.models import Delivery

    try:
        delivery = Delivery.objects.select_related(
            "order__client", "driver"
        ).get(pk=delivery_id)
    except Delivery.DoesNotExist:
        logger.error("Livraison #%d introuvable pour notification.", delivery_id)
        return

    # Notification au client avec code OTP
    client_msg = (
        f"AgriDirect: Livreur assigné! {delivery.driver.get_full_name()} "
        f"({delivery.driver.phone_number}) viendra chercher votre commande. "
        f"Votre code de confirmation: {delivery.otp_code}. "
        f"NE DONNEZ ce code qu'au livreur à la réception."
    )
    send_sms(delivery.order.client.phone_number, client_msg)

    # Notification au livreur
    driver_msg = (
        f"AgriDirect: Nouvelle course #{delivery.pk}! "
        f"Récupérez la commande chez le producteur. "
        f"Frais: {delivery.delivery_fee} FCFA."
    )
    send_sms(delivery.driver.phone_number, driver_msg)

    logger.info("Notifications envoyées pour livraison #%d.", delivery_id)
