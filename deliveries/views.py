"""
Vues API pour l'application Deliveries.

Gère la mise à jour du statut de livraison et la validation OTP.
"""

import logging

from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

from .models import Delivery
from orders.models import Order
from .serializers import (
    DeliverySerializer,
    DeliveryUpdateSerializer,
    DriverDeliveryListSerializer,
)
from .services import update_delivery_status, report_dispute

logger = logging.getLogger(__name__)


class DeliveryUpdateView(APIView):
    """
    PATCH /api/deliveries/{id}/

    Met à jour le statut d'une livraison par le livreur.

    Transitions :
        ASSIGNED → EN_ROUTE_PICKUP → PICKED_UP → EN_ROUTE_DELIVERY → DELIVERED

    Pour la transition vers DELIVERED, le code OTP est obligatoire.
    """

    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, pk):
        """
        Met à jour le statut de la livraison.

        Body:
            status (str): Nouveau statut.
            otp_code (str, optionnel): Code OTP pour finaliser.

        Returns:
            200: Livraison mise à jour.
            400: Transition invalide ou OTP incorrect.
            403: N'est pas le livreur assigné.
            404: Livraison introuvable.
        """
        try:
            delivery = Delivery.objects.select_related(
                "order", "order__client", "order__stock__product", "driver"
            ).get(pk=pk)
        except Delivery.DoesNotExist:
            return Response(
                {"detail": "Livraison introuvable."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Vérifier que c'est bien le livreur assigné
        if delivery.driver != request.user:
            return Response(
                {"detail": "Vous n'êtes pas le livreur assigné à cette livraison."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = DeliveryUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            delivery = update_delivery_status(
                delivery=delivery,
                new_status=serializer.validated_data["status"],
                otp_code=serializer.validated_data.get("otp_code"),
                driver_instance=request.user,
            )
        except ValueError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            DeliverySerializer(delivery).data,
            status=status.HTTP_200_OK,
        )


class DeliveryDetailView(APIView):
    """
    GET /api/deliveries/{id}/

    Récupère les détails d'une livraison.
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        """
        Retourne les détails d'une livraison.

        Accessible par le livreur assigné ou le client de la commande.
        """
        try:
            delivery = Delivery.objects.select_related(
                "order", "order__client", "order__stock__product", "driver"
            ).get(pk=pk)
        except Delivery.DoesNotExist:
            return Response(
                {"detail": "Livraison introuvable."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Vérifier l'accès
        user = request.user
        if user != delivery.driver and user != delivery.order.client:
            return Response(
                {"detail": "Accès refusé."},
                status=status.HTTP_403_FORBIDDEN,
            )

        return Response(
            DeliverySerializer(delivery).data,
            status=status.HTTP_200_OK,
        )


class DriverDeliveryListView(APIView):
    """
    GET /api/driver/deliveries/

    Liste des livraisons du livreur connecté.
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """
        Retourne les livraisons assignées au livreur.
        """
        if not request.user.is_livreur:
            return Response(
                {"detail": "Seuls les livreurs peuvent accéder à cette ressource."},
                status=status.HTTP_403_FORBIDDEN,
            )

        deliveries = (
            Delivery.objects.filter(driver=request.user)
            .select_related("order", "order__client", "order__stock__product")
            .order_by("-created_at")
        )

        serializer = DriverDeliveryListSerializer(deliveries, many=True)
        return Response(
            {
                "count": len(serializer.data),
                "results": serializer.data,
            },
            status=status.HTTP_200_OK,
        )


class DisputeView(APIView):
    """
    POST /api/orders/{id}/dispute/
    Signale un litige sur une commande.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            order = Order.objects.select_related('stock__producer').get(pk=pk)
        except Order.DoesNotExist:
            return Response({"detail": "Commande introuvable."}, status=status.HTTP_404_NOT_FOUND)

        user = request.user
        # Vérifier si l'utilisateur est impliqué
        is_involved = user == order.client or user == order.stock.producer
        if not is_involved and hasattr(order, 'delivery'):
             is_involved = user == order.delivery.driver

        if not is_involved:
            return Response({"detail": "Non autorisé."}, status=status.HTTP_403_FORBIDDEN)

        reason = request.data.get("reason", "Inconnue")
        report_dispute(order, reason, user)
        return Response({"detail": "Litige signalé."}, status=status.HTTP_200_OK)


class DeliveryUIView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """
    Vue pour afficher l'interface graphique mobile du livreur.
    """
    template_name = "deliveries/driver_app.html"
    login_url = "/admin/login/"

    def test_func(self):
        # Accessible par le staff ou les livreurs authentifiés
        return self.request.user.is_staff or self.request.user.is_livreur
