"""
Vues API pour l'application Accounts.

Gère l'inscription, le profil, la localisation des livreurs et le portefeuille.
"""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import (
    DriverLocationSerializer,
    UserProfileSerializer,
    UserRegistrationSerializer,
    WalletSerializer,
    WalletDepositSerializer,
)
from .models import Wallet


class RegisterView(generics.CreateAPIView):
    """
    POST /api/register/
    Inscrit un nouvel utilisateur (Producteur, Client ou Livreur).
    """
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]


class ProfileView(generics.RetrieveUpdateAPIView):
    """
    GET/PATCH /api/profile/
    Récupère ou met à jour le profil de l'utilisateur connecté.
    """
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class UpdateDriverLocationView(APIView):
    """
    POST /api/driver/location/
    Met à jour la position GPS du livreur en temps réel.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        if not request.user.is_livreur:
            return Response(
                {"detail": "Seuls les livreurs peuvent mettre à jour leur position."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = DriverLocationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        request.user.current_location_lat = serializer.validated_data["latitude"]
        request.user.current_location_lng = serializer.validated_data["longitude"]
        request.user.save(update_fields=["current_location_lat", "current_location_lng"])

        return Response(
            {"detail": "Position mise à jour avec succès."},
            status=status.HTTP_200_OK,
        )


class WalletView(generics.RetrieveAPIView):
    """
    GET /api/wallet/
    Affiche le solde et l'historique des transactions de l'utilisateur.
    """
    serializer_class = WalletSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        wallet, _ = Wallet.objects.get_or_create(user=self.request.user)
        return wallet


class WalletDepositView(APIView):
    """
    POST /api/wallet/recharge/
    Recharge le portefeuille (simulation pour le moment).
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = WalletDepositSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        amount = serializer.validated_data['amount']
        
        wallet, _ = Wallet.objects.get_or_create(user=request.user)
        wallet.deposit(amount, f"Recharge via Mobile Money (Simulé)")
        
        return Response(WalletSerializer(wallet).data, status=status.HTTP_200_OK)


class ProfileUIView(LoginRequiredMixin, TemplateView):
    """
    Vue pour afficher et modifier le profil utilisateur sur le web.
    """
    template_name = "accounts/profile.html"
    login_url = "/login/"
