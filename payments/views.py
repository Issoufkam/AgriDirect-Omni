from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, OpenApiResponse

from orders.models import Order
from payments.services import MobileMoneyService
from payments.serializers import PaymentInitializeSerializer

class InitializePaymentView(generics.GenericAPIView):
    """
    Initialise une transaction de paiement avec un opérateur Mobile Money.
    L'utilisateur (Client) choisit son fournisseur (Wave, Orange, etc.)
    et lance le paiement.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = PaymentInitializeSerializer

    @extend_schema(
        summary="Initialiser un paiement Mobile Money",
        description="Crée une intention de paiement et retourne une URL de redirection (mockée).",
        responses={200: OpenApiResponse(description="Paiement initialisé avec succès")}
    )
    def post(self, request, pk, *args, **kwargs):
        # Only client can pay for their order
        order = get_object_or_404(Order, pk=pk, client=request.user)

        if order.payment_status != Order.PaymentStatus.UNPAID:
            return Response(
                {"detail": "La commande est déjà payée ou en cours de paiement."},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        provider = serializer.validated_data["provider"]

        # Initialiser via le service mock
        response_data = MobileMoneyService.initialize_payment(order, provider)

        # Mettre à jour la commande avec l'ID transaction pour référence
        order.transaction_id = response_data["transaction_id"]
        order.payment_provider = provider
        # L'état reste UNPAID jusqu'au Webhook
        order.save(update_fields=["transaction_id", "payment_provider"])

        return Response(response_data, status=status.HTTP_200_OK)


class MobileMoneyWebhookView(generics.GenericAPIView):
    """
    Endpoint pour recevoir le callback asynchrone sécurisé du fournisseur
    Mobile Money (Wave/Orange Money) quand le client a validé le paiement sur son app.
    """
    permission_classes = [AllowAny]
    authentication_classes = [] # Le fournisseur n'utilise pas notre JWT

    @extend_schema(
        summary="Webhook - Callback de Paiement (Mobile Money)",
        description="Reçoit la notification de statut final de paiement (SUCCESS/FAILED) depuis le fournisseur Mobile Money.",
        responses={200: OpenApiResponse(description="Webhook traité avec succès")}
    )
    def post(self, request, *args, **kwargs):
        payload = request.data
        # On suppose que le payload contient { "transaction_id": "MOCK-...", "status": "SUCCESS" }
        success = MobileMoneyService.process_webhook(payload)

        if success:
            return Response({"message": "Webhook traité avec succès, paiement mis sous séquestre."}, status=status.HTTP_200_OK)
        else:
            return Response({"message": "Webhook ignoré ou transaction introuvable/échouée."}, status=status.HTTP_400_BAD_REQUEST)
