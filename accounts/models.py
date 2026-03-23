"""
Modèles pour l'application Accounts.

Définit le modèle CustomUser qui hérite de AbstractUser avec
authentification par numéro de téléphone et système de rôles.

Compatible PostGIS (production) et SQLite (développement).
"""

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models

from .managers import CustomUserManager

# ── Compatibilité PostGIS / SQLite ──
HAS_GIS = "django.contrib.gis" in settings.INSTALLED_APPS

if HAS_GIS:
    from django.contrib.gis.db import models as gis_models


class CustomUser(AbstractUser):
    """
    Utilisateur personnalisé identifié par son numéro de téléphone.

    Rôles principaux : PRODUCTEUR, CLIENT, LIVREUR.
    Sous-rôles (pour les producteurs) : PLANTEUR, PECHEUR, BERGER, BOUCHER, ELEVEUR.
    """

    class Role(models.TextChoices):
        PRODUCTEUR = "PRODUCTEUR", "Producteur"
        CLIENT = "CLIENT", "Client"
        LIVREUR = "LIVREUR", "Livreur"

    class SubRole(models.TextChoices):
        PLANTEUR = "PLANTEUR", "Planteur"
        PECHEUR = "PECHEUR", "Pêcheur"
        BERGER = "BERGER", "Berger"
        BOUCHER = "BOUCHER", "Boucher"
        ELEVEUR = "ELEVEUR", "Éleveur"
        NONE = "", "Aucun"

    # Le username n'est plus utilisé, on utilise phone_number
    username = None

    phone_number = models.CharField(
        "numéro de téléphone",
        max_length=20,
        unique=True,
        db_index=True,
        help_text="Identifiant unique de l'utilisateur (format: +225XXXXXXXXXX).",
    )

    role = models.CharField(
        "rôle",
        max_length=15,
        choices=Role.choices,
        default=Role.CLIENT,
    )

    sub_role = models.CharField(
        "sous-rôle",
        max_length=15,
        choices=SubRole.choices,
        default=SubRole.NONE,
        blank=True,
    )

    avatar = models.ImageField(
        "avatar",
        upload_to="avatars/",
        null=True,
        blank=True,
    )

    is_verified = models.BooleanField(
        "vérifié",
        default=False,
        help_text="Indique si le compte a été vérifié par SMS.",
    )

    # ── Champs spécifiques aux livreurs ──
    is_active_driver = models.BooleanField(
        "livreur actif",
        default=False,
        help_text="Le livreur est-il actuellement disponible pour des courses ?",
    )

    has_refrigeration = models.BooleanField(
        "équipement réfrigéré",
        default=False,
        help_text="Le livreur dispose-t-il d'un équipement de transport réfrigéré ?",
    )

    # Localisation — compatible PostGIS et SQLite
    current_location_lat = models.FloatField(
        "latitude actuelle",
        null=True,
        blank=True,
    )
    current_location_lng = models.FloatField(
        "longitude actuelle",
        null=True,
        blank=True,
    )

    # ── Auth settings ──
    USERNAME_FIELD = "phone_number"
    REQUIRED_FIELDS = ["first_name", "last_name", "role"]

    objects = CustomUserManager()

    class Meta:
        verbose_name = "utilisateur"
        verbose_name_plural = "utilisateurs"
        ordering = ["-date_joined"]

    def __str__(self):
        return f"{self.get_full_name()} ({self.phone_number})"

    @property
    def is_producteur(self) -> bool:
        """Vérifie si l'utilisateur est un producteur."""
        return self.role == self.Role.PRODUCTEUR

    @property
    def is_client(self) -> bool:
        """Vérifie si l'utilisateur est un client."""
        return self.role == self.Role.CLIENT

    @property
    def is_livreur(self) -> bool:
        """Vérifie si l'utilisateur est un livreur."""
        return self.role == self.Role.LIVREUR

    @property
    def has_location(self) -> bool:
        """Vérifie si l'utilisateur a une position GPS."""
        return self.current_location_lat is not None and self.current_location_lng is not None

    @property
    def average_rating(self) -> float:
        """
        Calcule la note moyenne de l'utilisateur.
        - Pour un Producteur: moyenne des avis 'PRODUIT' sur ses ordres.
        - Pour un Livreur: moyenne des avis 'LIVREUR' sur ses livraisons.
        """
        from reviews.models import Review
        from django.db.models import Avg

        if self.is_producteur:
            ratings = Review.objects.filter(
                order__stock__producer=self,
                target_type=Review.Target.PRODUIT
            ).aggregate(avg=Avg('rating'))['avg']
            return round(ratings, 1) if ratings else 0.0

        if self.is_livreur:
            ratings = Review.objects.filter(
                order__delivery__driver=self,
                target_type=Review.Target.LIVREUR
            ).aggregate(avg=Avg('rating'))['avg']
            return round(ratings, 1) if ratings else 0.0

        return 0.0


class UserActivity(models.Model):
    """
    Journalise l'activité brute des utilisateurs (clics, pages vues).
    Utilisé pour l'analytique et l'amélioration de l'expérience utilisateur.
    """
    user = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True)
    session_key = models.CharField(max_length=40, null=True, blank=True)
    tracking_id = models.CharField(max_length=100, db_index=True, help_text="ID unique stocké en cookie.")
    
    ip_address = models.GenericIPAddressField(null=True)
    user_agent = models.TextField(null=True)
    path = models.CharField(max_length=255)
    method = models.CharField(max_length=10)
    
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "activité utilisateur"
        verbose_name_plural = "activités utilisateurs"
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.tracking_id} -> {self.path} ({self.timestamp})"
