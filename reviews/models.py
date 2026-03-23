from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

class Review(models.Model):
    """
    Système de notation pour la confiance de la plateforme.
    Un client peut évaluer la qualité du produit/producteur ET du livreur.
    """

    class Target(models.TextChoices):
        PRODUIT = "PRODUIT", "Produit/Producteur"
        LIVREUR = "LIVREUR", "Livreur / Service de livraison"

    order = models.ForeignKey(
        "orders.Order",
        on_delete=models.CASCADE,
        related_name="reviews",
        verbose_name="commande",
    )

    client = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reviews_given",
        verbose_name="client",
    )

    target_type = models.CharField(
        "cible de l'avis",
        max_length=15,
        choices=Target.choices,
    )

    rating = models.PositiveSmallIntegerField(
        "note (1-5)",
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )

    comment = models.TextField(
        "commentaire",
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "avis"
        verbose_name_plural = "avis"
        ordering = ["-created_at"]
        # Un client ne peut noter une cible donnée qu'une seule fois par commande
        unique_together = ["order", "target_type"]

    def __str__(self):
        return f"Avis {self.target_type} - {self.rating}/5 - Order #{self.order_id}"
