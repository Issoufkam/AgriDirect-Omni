"""
Modèles pour l'application Deliveries.

Gère les courses de livraison avec code OTP de validation.
"""

import secrets

from django.conf import settings
from django.db import models


class Delivery(models.Model):
    """
    Course de livraison assignée à un livreur.

    Le code OTP est généré automatiquement et communiqué au client.
    Le livreur doit obtenir ce code du client pour finaliser la livraison.
    L'argent en séquestre n'est libéré qu'après validation du code OTP.
    """

    class Status(models.TextChoices):
        ASSIGNED = "ASSIGNED", "Assignée"
        EN_ROUTE_PICKUP = "EN_ROUTE_PICKUP", "En route vers le producteur"
        PICKED_UP = "PICKED_UP", "Produit récupéré"
        EN_ROUTE_DELIVERY = "EN_ROUTE_DELIVERY", "En route vers le client"
        DELIVERED = "DELIVERED", "Livrée"
        CANCELLED = "CANCELLED", "Annulée"

    order = models.OneToOneField(
        "orders.Order",
        on_delete=models.CASCADE,
        related_name="delivery",
        verbose_name="commande",
    )

    driver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="deliveries",
        verbose_name="livreur",
        limit_choices_to={"role": "LIVREUR"},
    )

    status = models.CharField(
        "statut",
        max_length=20,
        choices=Status.choices,
        default=Status.ASSIGNED,
        db_index=True,
    )

    delivery_fee = models.DecimalField(
        "frais de livraison (FCFA)",
        max_digits=10,
        decimal_places=0,
        help_text="Part des frais de livraison revenant au livreur.",
    )

    otp_code = models.CharField(
        "code OTP",
        max_length=6,
        help_text="Code secret à 6 chiffres pour valider la fin de course.",
    )

    pickup_time = models.DateTimeField(
        "heure de ramassage",
        null=True,
        blank=True,
    )

    delivery_time = models.DateTimeField(
        "heure de livraison",
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField("créée le", auto_now_add=True)
    updated_at = models.DateTimeField("mise à jour le", auto_now=True)

    class Meta:
        verbose_name = "livraison"
        verbose_name_plural = "livraisons"
        ordering = ["-created_at"]

    def __str__(self):
        return (
            f"Livraison #{self.pk} — Commande #{self.order_id} — "
            f"{self.driver.get_full_name()} — {self.get_status_display()}"
        )

    def save(self, *args, **kwargs):
        """Génère automatiquement un code OTP à la création."""
        if not self.otp_code:
            self.otp_code = self.generate_otp()
        super().save(*args, **kwargs)

    @staticmethod
    def generate_otp() -> str:
        """
        Génère un code OTP à 6 chiffres cryptographiquement sûr.

        Returns:
            Chaîne de 6 chiffres.
        """
        return f"{secrets.randbelow(1000000):06d}"
