"""
Vues API pour l'application Accounts.

Gère l'inscription, le profil et la localisation des livreurs.
"""

from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import (
    DriverLocationSerializer,
    UserProfileSerializer,
    UserRegistrationSerializer,
)


class RegisterView(generics.CreateAPIView):
    """
    POST /api/register/

    Inscrit un nouvel utilisateur (Producteur, Client ou Livreur).
    Accessible sans authentification.
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
        """Retourne l'utilisateur actuellement authentifié."""
        return self.request.user


class UpdateDriverLocationView(APIView):
    """
    POST /api/driver/location/

    Met à jour la position GPS du livreur en temps réel.
    Réservé aux utilisateurs avec rôle LIVREUR.
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        """
        Met à jour la position du livreur.

        Body:
            longitude (float): Longitude GPS.
            latitude (float): Latitude GPS.

        Returns:
            200: Position mise à jour.
            403: L'utilisateur n'est pas un livreur.
        """
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
