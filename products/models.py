"""
Modèles pour l'application Products.

Définit les produits agricoles et les stocks des producteurs.
Compatible PostGIS (production) et SQLite (développement).
"""

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


class Product(models.Model):
    """
    Produit référencé sur la plateforme avec prix national imposé.

    Le prix est fixé par l'État / la plateforme pour empêcher
    la spéculation. Les producteurs ne peuvent pas modifier ce prix.

    Catégories :
        - VIVRIER : Maïs, Riz, Igname, Manioc, Banane plantain, etc.
        - CARNE : Bœuf, Mouton, Chèvre, Poulet, etc.
        - HALIEUTIQUE : Carpe, Tilapia, Thon, Crevettes, etc.
        - ELEVAGE : Œufs, Lait, etc.
    """

    class Category(models.TextChoices):
        VIVRIER = "VIVRIER", "Vivrier"
        CARNE = "CARNE", "Carné"
        HALIEUTIQUE = "HALIEUTIQUE", "Halieutique"
        ELEVAGE = "ELEVAGE", "Élevage"

    class Unit(models.TextChoices):
        KG = "KG", "Kilogramme"
        TETE = "TETE", "Tête"
        SAC = "SAC", "Sac"
        CASIER = "CASIER", "Casier"
        TAS = "TAS", "Tas"

    name = models.CharField(
        "nom du produit",
        max_length=100,
        unique=True,
        db_index=True,
    )

    category = models.CharField(
        "catégorie",
        max_length=15,
        choices=Category.choices,
    )

    unit = models.CharField(
        "unité de mesure",
        max_length=10,
        choices=Unit.choices,
        default=Unit.KG,
    )

    national_price = models.DecimalField(
        "prix national (FCFA)",
        max_digits=10,
        decimal_places=0,
        validators=[MinValueValidator(0)],
        help_text="Prix imposé par l'État / la plateforme en FCFA.",
    )

    needs_refrigeration = models.BooleanField(
        "nécessite réfrigération",
        default=False,
        help_text="Indique si le produit est périssable et nécessite un transport réfrigéré.",
    )

    image = models.ImageField(
        "image",
        upload_to="products/",
        null=True,
        blank=True,
    )

    is_active = models.BooleanField(
        "actif",
        default=True,
        help_text="Produit disponible sur la plateforme.",
    )

    created_at = models.DateTimeField("créé le", auto_now_add=True)
    updated_at = models.DateTimeField("mis à jour le", auto_now=True)

    class Meta:
        verbose_name = "produit"
        verbose_name_plural = "produits"
        ordering = ["category", "name"]

    def __str__(self):
        return f"{self.name} ({self.get_unit_display()}) — {self.national_price} FCFA"


class Stock(models.Model):
    """
    Stock d'un producteur pour un produit donné.

    Chaque entrée représente une disponibilité de stock
    avec localisation GPS du producteur.
    """

    producer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="stocks",
        verbose_name="producteur",
        limit_choices_to={"role": "PRODUCTEUR"},
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="stocks",
        verbose_name="produit",
    )

    quantity = models.DecimalField(
        "quantité initiale",
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )

    remaining_quantity = models.DecimalField(
        "quantité restante",
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )

    # Localisation du stock — champs simples pour compatibilité SQLite/PostGIS
    location_lat = models.FloatField(
        "latitude du stock",
        help_text="Latitude GPS du lieu de stockage.",
    )
    location_lng = models.FloatField(
        "longitude du stock",
        help_text="Longitude GPS du lieu de stockage.",
    )

    needs_refrigeration = models.BooleanField(
        "nécessite réfrigération",
        default=False,
        help_text="Ce stock spécifique nécessite-t-il un transport réfrigéré ?",
    )

    created_at = models.DateTimeField("créé le", auto_now_add=True)
    updated_at = models.DateTimeField("mis à jour le", auto_now=True)

    dynamic_discount = models.DecimalField(
        "remise dynamique (%)",
        max_digits=3,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(0)],
    )

    class Meta:
        verbose_name = "stock"
        verbose_name_plural = "stocks"
        ordering = ["-created_at"]
        # Un producteur ne peut avoir qu'un seul stock actif par produit
        constraints = [
            models.UniqueConstraint(
                fields=["producer", "product"],
                name="unique_producer_product_stock",
            )
        ]

    def __str__(self):
        return (
            f"{self.producer.get_full_name()} — "
            f"{self.product.name}: {self.remaining_quantity} {self.product.get_unit_display()}"
        )

    @property
    def is_available(self) -> bool:
        """Vérifie si le stock a encore des quantités disponibles."""
        return self.remaining_quantity > 0

    @property
    def unit_price(self):
        """
        Retourne le prix unitaire calculé.
        Prix National - Remise Dynamique.
        """
        base_price = self.product.national_price
        if self.dynamic_discount > 0:
            discount_amount = base_price * self.dynamic_discount
            return (base_price - discount_amount).quantize(base_price)
        return base_price
