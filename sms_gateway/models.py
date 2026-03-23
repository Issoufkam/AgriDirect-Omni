"""
Modèles pour l'application SMS Gateway.

Journalise les SMS entrants et sortants pour audit.
"""

from django.conf import settings
from django.db import models


class SMSLog(models.Model):
    """
    Journal des SMS traités par la plateforme.

    Enregistre chaque SMS entrant (INBOUND) et les réponses
    envoyées (OUTBOUND) pour traçabilité et débogage.
    """

    class Direction(models.TextChoices):
        INBOUND = "INBOUND", "Entrant"
        OUTBOUND = "OUTBOUND", "Sortant"

    class Status(models.TextChoices):
        RECEIVED = "RECEIVED", "Reçu"
        PARSED = "PARSED", "Analysé"
        PROCESSED = "PROCESSED", "Traité"
        ERROR = "ERROR", "Erreur"
        SENT = "SENT", "Envoyé"

    direction = models.CharField(
        "direction",
        max_length=10,
        choices=Direction.choices,
    )

    phone_number = models.CharField(
        "numéro de téléphone",
        max_length=20,
        db_index=True,
    )

    raw_text = models.TextField(
        "texte brut",
        help_text="Contenu du SMS tel que reçu ou envoyé.",
    )

    parsed_data = models.JSONField(
        "données extraites",
        null=True,
        blank=True,
        help_text="Résultat du parsing (produit, quantité, unité).",
    )

    status = models.CharField(
        "statut",
        max_length=15,
        choices=Status.choices,
        default=Status.RECEIVED,
    )

    error_message = models.TextField(
        "message d'erreur",
        blank=True,
        default="",
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sms_logs",
        verbose_name="utilisateur",
    )

    created_at = models.DateTimeField("créé le", auto_now_add=True)

    class Meta:
        verbose_name = "journal SMS"
        verbose_name_plural = "journaux SMS"
        ordering = ["-created_at"]

    def __str__(self):
        return (
            f"[{self.get_direction_display()}] {self.phone_number}: "
            f"{self.raw_text[:50]}..."
        )
