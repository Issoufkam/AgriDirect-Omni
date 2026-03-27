"""
Modèles pour l'application Orders.

Gère les commandes des clients avec système de séquestre
et intégration Mobile Money.
"""

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


class Order(models.Model):
    """
    Commande passée par un client.

    Le prix est automatiquement calculé à partir du national_price
    du produit. Le système de séquestre retient l'argent jusqu'à
    la validation OTP par le client.

    Statuts :
        PENDING    → Commande créée, en attente de livreur.
        ASSIGNED   → Livreur assigné, en route vers le producteur.
        PICKED_UP  → Produit récupéré, en route vers le client.
        DELIVERED  → Livraison terminée, code OTP validé.
        CANCELLED  → Commande annulée.
    """

    class Status(models.TextChoices):
        PENDING = "PENDING", "En attente"
        ASSIGNED = "ASSIGNED", "Livreur assigné"
        PICKED_UP = "PICKED_UP", "Récupérée"
        DELIVERED = "DELIVERED", "Livrée"
        CANCELLED = "CANCELLED", "Annulée"
        DISPUTED = "DISPUTED", "Litige en cours"

    class PaymentStatus(models.TextChoices):
        UNPAID = "UNPAID", "Non payé"
        ESCROWED = "ESCROWED", "En séquestre"
        RELEASED = "RELEASED", "Libéré au producteur"
        REFUNDED = "REFUNDED", "Remboursé"

    client = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="orders",
        verbose_name="client",
        limit_choices_to={"role": "CLIENT"},
    )

    stock = models.ForeignKey(
        "products.Stock",
        on_delete=models.PROTECT,
        related_name="orders",
        verbose_name="stock",
        help_text="Stock du producteur à partir duquel la commande est passée.",
    )

    quantity = models.DecimalField(
        "quantité commandée",
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
    )

    unit_price = models.DecimalField(
        "prix unitaire (FCFA)",
        max_digits=10,
        decimal_places=0,
        help_text="Prix national imposé au moment de la commande.",
    )

    total_product_amount = models.DecimalField(
        "montant produits (FCFA)",
        max_digits=12,
        decimal_places=0,
        help_text="= quantité × prix unitaire.",
    )

    delivery_fee = models.DecimalField(
        "frais de livraison (FCFA)",
        max_digits=10,
        decimal_places=0,
        default=0,
    )

    total_amount = models.DecimalField(
        "montant total (FCFA)",
        max_digits=12,
        decimal_places=0,
        help_text="= montant produits + frais de livraison.",
    )

    status = models.CharField(
        "statut",
        max_length=15,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )

    delivery_address = models.TextField(
        "adresse de livraison",
        help_text="Adresse textuelle de livraison.",
    )

    # Localisation du client — champs simples
    client_location_lat = models.FloatField(
        "latitude du client",
        help_text="Latitude GPS du client.",
    )
    client_location_lng = models.FloatField(
        "longitude du client",
        help_text="Longitude GPS du client.",
    )

    # ── Paiement Mobile Money ──
    payment_status = models.CharField(
        "statut de paiement",
        max_length=15,
        choices=PaymentStatus.choices,
        default=PaymentStatus.UNPAID,
    )

    transaction_id = models.CharField(
        "ID transaction Mobile Money",
        max_length=100,
        blank=True,
        default="",
        help_text="Référence de paiement Wave / Orange Money / MTN MoMo.",
    )

    payment_provider = models.CharField(
        "fournisseur de paiement",
        max_length=20,
        blank=True,
        default="",
        help_text="WAVE, ORANGE_MONEY, MTN_MOMO.",
    )

    # ── Timestamps ──
    created_at = models.DateTimeField("créée le", auto_now_add=True)
    updated_at = models.DateTimeField("mise à jour le", auto_now=True)

    class Meta:
        verbose_name = "commande"
        verbose_name_plural = "commandes"
        ordering = ["-created_at"]

    def __str__(self):
        return (
            f"Commande #{self.pk} — {self.client.get_full_name()} — "
            f"{self.get_status_display()} — {self.total_amount} FCFA"
        )

    @property
    def producer(self):
        """Retourne le producteur associé via le stock."""
        return self.stock.producer

    @property
    def product(self):
        """Retourne le produit associé via le stock."""
        return self.stock.product
