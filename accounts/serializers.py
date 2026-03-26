"""
Serializers pour l'application Accounts.

Gère la sérialisation/désérialisation des données utilisateur
pour l'API REST.
"""

from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import Wallet, Transaction

User = get_user_model()


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer pour l'inscription d'un nouvel utilisateur.

    Valide le numéro de téléphone, le rôle et crée l'utilisateur.
    """

    password = serializers.CharField(write_only=True, min_length=6, required=False)

    class Meta:
        model = User
        fields = [
            "id",
            "phone_number",
            "first_name",
            "last_name",
            "role",
            "sub_role",
            "password",
        ]
        read_only_fields = ["id"]

    def validate_sub_role(self, value):
        """
        Valide que le sous-rôle est cohérent avec le rôle principal.

        Seuls les producteurs peuvent avoir un sous-rôle.
        """
        role = self.initial_data.get("role", "")
        if value and role != User.Role.PRODUCTEUR:
            raise serializers.ValidationError(
                "Seuls les producteurs peuvent avoir un sous-rôle."
            )
        return value

    def create(self, validated_data):
        """Crée l'utilisateur via le manager personnalisé."""
        password = validated_data.pop("password", None)
        return User.objects.create_user(password=password, **validated_data)


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer pour le profil utilisateur (lecture/mise à jour).
    """

    class Meta:
        model = User
        fields = [
            "id",
            "phone_number",
            "first_name",
            "last_name",
            "role",
            "sub_role",
            "avatar",
            "is_verified",
            "is_active_driver",
            "has_refrigeration",
            "date_joined",
        ]
        read_only_fields = [
            "id",
            "phone_number",
            "role",
            "is_verified",
            "date_joined",
        ]


class DriverLocationSerializer(serializers.Serializer):
    """
    Serializer pour la mise à jour de la position du livreur.
    """

    longitude = serializers.FloatField(min_value=-180, max_value=180)
    latitude = serializers.FloatField(min_value=-90, max_value=90)


class TransactionSerializer(serializers.ModelSerializer):
    """Serializer pour l'historique des transactions."""
    date = serializers.DateTimeField(source="timestamp", format="%d/%m/%Y %H:%M")

    class Meta:
        model = Transaction
        fields = ["amount", "description", "date"]


class WalletSerializer(serializers.ModelSerializer):
    """Serializer pour le portefeuille utilisateur."""
    transactions = TransactionSerializer(many=True, read_only=True)

    class Meta:
        model = Wallet
        fields = ["balance", "transactions"]


class WalletDepositSerializer(serializers.Serializer):
    """Serializer pour le dépôt d'argent (recharge)."""
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=100)
