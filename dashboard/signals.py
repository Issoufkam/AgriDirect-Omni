from django.db.models.signals import post_save
from django.dispatch import receiver
from orders.models import Order
from products.models import Stock
from sms_gateway.notifications import send_push_notification
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Order)
def notify_producer_new_order(sender, instance, created, **kwargs):
    """
    Notifie le producteur dès qu'une nouvelle commande est passée.
    """
    if created:
        producer = instance.stock.producer
        token = producer.expo_push_token
        
        if token:
            message = f"📢 Nouvelle commande ! {instance.quantity} {instance.stock.unit} de {instance.stock.product.name} viennent d'être achetés."
            success = send_push_notification(token, message, extra_data={"order_id": instance.id, "type": "new_order"})
            if success:
                logger.info(f"Notification envoyée au producteur {producer.phone_number} pour l'ordre #{instance.id}")

@receiver(post_save, sender=Stock)
def notify_producer_low_stock(sender, instance, **kwargs):
    """
    Alerte le producteur quand son stock tombe sous un seuil critique (20%).
    """
    # On ne notifie que si le stock n'est pas déjà à zéro (pour éviter les doublons)
    if 0 < instance.remaining_quantity <= (instance.quantity * 0.2):
        producer = instance.producer
        token = producer.expo_push_token
        
        if token:
            # Calcul du pourcentage restant pour un message plus précis
            percent = int((instance.remaining_quantity / instance.quantity) * 100)
            message = f"⚠️ Stock Critique ! Il ne reste que {instance.remaining_quantity} {instance.unit} de {instance.product.name} ({percent}% restant)."
            
            # On envoie la notification
            send_push_notification(token, message, extra_data={"stock_id": instance.id, "type": "low_stock"})
            logger.info(f"Alerte stock bas envoyée à {producer.phone_number} pour {instance.product.name}")
