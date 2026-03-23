"""
Vues API pour l'application Orders.

Création et gestion des commandes.
"""

import logging

from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

from .serializers import OrderCreateSerializer, OrderSerializer
from .services import cancel_order, create_order

logger = logging.getLogger(__name__)


class OrderCreateView(APIView):
    """
    POST /api/orders/

    Crée une nouvelle commande avec calcul automatique des frais.

    Le prix est imposé par le national_price du produit.
    Les frais de livraison sont calculés selon la distance Haversine.
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        """
        Crée une commande.

        Body:
            stock_id (int): ID du stock à commander.
            quantity (float): Quantité souhaitée.
            delivery_address (str): Adresse de livraison.
            client_lat (float): Latitude du client.
            client_lng (float): Longitude du client.

        Returns:
            201: Commande créée avec détails complets.
            400: Données invalides ou stock insuffisant.
            403: L'utilisateur n'est pas un client.
        """
        if not request.user.is_client:
            return Response(
                {"detail": "Seuls les clients peuvent passer des commandes."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = OrderCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            order = create_order(
                client=request.user,
                stock_id=serializer.validated_data["stock_id"],
                quantity=serializer.validated_data["quantity"],
                delivery_address=serializer.validated_data["delivery_address"],
                client_lat=serializer.validated_data["client_lat"],
                client_lng=serializer.validated_data["client_lng"],
            )
        except ValueError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            OrderSerializer(order).data,
            status=status.HTTP_201_CREATED,
        )


class OrderListView(APIView):
    """
    GET /api/orders/

    Liste les commandes de l'utilisateur connecté.
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """
        Retourne les commandes de l'utilisateur.

        - CLIENT : ses propres commandes.
        - PRODUCTEUR : commandes liées à ses stocks.
        - LIVREUR : commandes qui lui sont assignées.
        """
        user = request.user

        if user.is_client:
            orders = user.orders.all()
        elif user.is_producteur:
            from orders.models import Order
            orders = Order.objects.filter(stock__producer=user)
        elif user.is_livreur:
            from orders.models import Order
            orders = Order.objects.filter(delivery__driver=user)
        else:
            orders = Order.objects.none()

        orders = orders.select_related(
            "stock__product", "stock__producer", "client"
        ).order_by("-created_at")

        serializer = OrderSerializer(orders, many=True)
        return Response(
            {
                "count": len(serializer.data),
                "results": serializer.data,
            },
            status=status.HTTP_200_OK,
        )


class OrderCancelView(APIView):
    """
    POST /api/orders/{id}/cancel/

    Annule une commande (PENDING ou ASSIGNED uniquement).
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        """
        Annule une commande et restitue le stock.

        Returns:
            200: Commande annulée.
            400: Commande non annulable.
            404: Commande introuvable.
        """
        from orders.models import Order

        try:
            order = Order.objects.get(pk=pk, client=request.user)
        except Order.DoesNotExist:
            return Response(
                {"detail": "Commande introuvable."},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            order = cancel_order(order)
        except ValueError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            OrderSerializer(order).data,
            status=status.HTTP_200_OK,
        )


class OrderHistoryUIView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """
    Vue pour afficher l'historique des commandes du client.
    Permet aussi de soumettre des avis sur les commandes livrées.
    """
    template_name = "orders/history.html"
    login_url = "/admin/login/"

    def test_func(self):
        # Accessible par le staff ou les clients authentifiés
        return self.request.user.is_staff or self.request.user.is_client
