import logging
import uuid
from typing import Dict, Any

from django.conf import settings
from orders.models import Order
from sms_gateway.services import send_sms
from deliveries.services import auto_dispatch_order

logger = logging.getLogger(__name__)


class MobileMoneyService:
    """
    Mock Service pour l'intégration de paiements Mobile Money
    (Wave, Orange Money, MTN MoMo).
    """

    SUPPORTED_PROVIDERS = ["WAVE", "ORANGE_MONEY", "MTN_MOMO"]

    @classmethod
    def initialize_payment(cls, order: Order, provider: str) -> Dict[str, Any]:
        """
        Initialise une demande de paiement auprès d'un opérateur Mobile Money.
        """
        if provider not in cls.SUPPORTED_PROVIDERS:
            raise ValueError(f"Fournisseur non supporté: {provider}. Options: {cls.SUPPORTED_PROVIDERS}")

        # Dans un cas réel, nous ferions une requête HTTP à l'API du fournisseur.
        # Ici on simule une réponse réussie.
        transaction_id = f"MOCK-{provider}-{uuid.uuid4().hex[:8].upper()}"

        logger.info(f"Payment initialized for order {order.id} via {provider}. TxID: {transaction_id}")

        return {
            "success": True,
            "payment_url": f"https://mock-{provider.lower()}-gateway.com/pay/{transaction_id}",
            "transaction_id": transaction_id,
            "amount": float(order.total_amount),
            "currency": "FCFA",
        }

    @classmethod
    def process_webhook(cls, payload: Dict[str, Any]) -> bool:
        """
        Gère le webhook envoyé par le fournisseur Mobile Money indiquant
        qu'un paiement a réussi.
        """
        transaction_id = payload.get("transaction_id")
        status = payload.get("status")

        if not transaction_id or status != "SUCCESS":
            logger.warning(f"Webhook failed or status not SUCCESS: {payload}")
            return False

        try:
            order = Order.objects.get(transaction_id=transaction_id)
            if order.payment_status == Order.PaymentStatus.UNPAID:
                # Le paiement est reçu, l'argent est mis sous séquestre
                order.payment_status = Order.PaymentStatus.ESCROWED
                order.save(update_fields=["payment_status", "updated_at"])
                logger.info(f"Order {order.id} payment secured (ESCROWED) with TxID {transaction_id}.")
                
                # ── Notification SMS au Producteur ──
                producer_msg = (
                    f"AgriDirect: Nouvelle commande #{order.id}! "
                    f"Produit: {order.product.name} ({order.quantity} {order.order_unit}). "
                    f"Préparez le stock pour l'enlèvement."
                )
                send_sms(str(order.producer.phone_number), producer_msg)
                
                # ── Notification SMS au Client ──
                client_msg = (
                    f"AgriDirect: Paiement reçu pour la commande #{order.id}. "
                    f"Votre argent est protégé sous séquestre jusqu'à la livraison."
                )
                send_sms(str(order.client.phone_number), client_msg)

                # ── Auto-Dispatch au Livreur le plus proche ──
                delivery = auto_dispatch_order(order)
                if delivery:
                    # Notification au Livreur (SMS)
                    driver_msg = (
                        f"AgriDirect: Nouvelle mission #{delivery.id}! "
                        f"Collecte: {order.producer.get_full_name()} "
                        f"→ Destination: {order.delivery_address}. "
                        "Consultez votre app Livreur."
                    )
                    send_sms(str(delivery.driver.phone_number), driver_msg)

                return True
        except Order.DoesNotExist:
            logger.error(f"Webhook received for unknown transaction id: {transaction_id}")

        return False

    @classmethod
    def release_escrow(cls, order: Order) -> bool:
        """
        Libère l'argent du producteur et du livreur suite à la livraison.
        Appelé une fois la commande marquée DELIVERED et l'OTP validé.
        """
        if order.payment_status != Order.PaymentStatus.ESCROWED:
            logger.warning(f"Cannot release escrow for order {order.id} with status {order.payment_status}")
            return False

        # Dans un cas réel, requête au fournisseur pour transférer les fonds au compte producteur/livreur
        # Simulation d'un transfert réussi
        logger.info(f"Funds for order {order.id} released to Producer and Driver.")
        
        order.payment_status = Order.PaymentStatus.RELEASED
        order.save(update_fields=["payment_status", "updated_at"])

        # ── Notification SMS au Producteur (Paiement versé) ──
        producer_payment_msg = (
            f"AgriDirect: Livraison confirmée pour #{order.id}. "
            f"Les fonds ont été versés sur votre compte Mobile Money. Merci !"
        )
        send_sms(str(order.producer.phone_number), producer_payment_msg)

        return True
