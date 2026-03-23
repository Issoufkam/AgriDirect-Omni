"""
Vues API pour l'application SMS Gateway.

Webhook pour recevoir les SMS des producteurs.
"""

import logging

from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .services import SMSParseError, process_stock_sms

logger = logging.getLogger("sms_gateway")


class SMSWebhookView(APIView):
    """
    POST /api/sms-webhook/

    Webhook pour recevoir les SMS des producteurs et mettre à jour
    leurs stocks automatiquement.

    Ce endpoint est appelé par le gateway SMS (Africa's Talking)
    ou directement pour les tests.

    Accessible sans authentification JWT (l'authentification se fait
    par numéro de téléphone dans le corps du SMS).
    """

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        """
        Traite un SMS entrant.

        Body:
            from / phone_number (str): Numéro de téléphone de l'expéditeur.
            text / message (str): Contenu du SMS.
            latitude (float, optionnel): Latitude GPS.
            longitude (float, optionnel): Longitude GPS.

        Returns:
            200: SMS traité avec succès.
            400: Erreur de parsing ou données manquantes.
        """
        # Africa's Talking utilise 'from' et 'text'
        # On supporte aussi 'phone_number' et 'message' pour les tests
        phone_number = (
            request.data.get("from")
            or request.data.get("phone_number")
            or request.data.get("phoneNumber")
        )
        raw_text = (
            request.data.get("text")
            or request.data.get("message")
        )

        if not phone_number or not raw_text:
            return Response(
                {
                    "success": False,
                    "detail": "Champs 'phone_number' et 'message' obligatoires.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Normaliser le numéro de téléphone
        phone_number = phone_number.strip()

        # Coordonnées GPS optionnelles
        latitude = request.data.get("latitude")
        longitude = request.data.get("longitude")

        if latitude is not None:
            try:
                latitude = float(latitude)
            except (TypeError, ValueError):
                latitude = None

        if longitude is not None:
            try:
                longitude = float(longitude)
            except (TypeError, ValueError):
                longitude = None

        try:
            result = process_stock_sms(
                phone_number=phone_number,
                raw_text=raw_text,
                latitude=latitude,
                longitude=longitude,
            )
            return Response(result, status=status.HTTP_200_OK)

        except SMSParseError as e:
            logger.warning("Erreur parsing SMS de %s: %s", phone_number, e)
            return Response(
                {
                    "success": False,
                    "detail": str(e),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        except Exception as e:
            logger.exception("Erreur inattendue traitement SMS de %s", phone_number)
            return Response(
                {
                    "success": False,
                    "detail": "Erreur interne. Réessayez plus tard.",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
