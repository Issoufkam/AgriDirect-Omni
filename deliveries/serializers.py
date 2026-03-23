"""
Serializers pour l'application Deliveries.
"""

from rest_framework import serializers
from .models import Delivery


class OrderDetailSerializer(serializers.Serializer):
    """Métadonnées de la commande pour le livreur."""
    id = serializers.IntegerField(source="pk")
    product_name = serializers.CharField(source="stock.product.name")
    quantity = serializers.DecimalField(max_digits=10, decimal_places=2)
    unit = serializers.CharField(source="stock.product.get_unit_display")
    delivery_address = serializers.CharField()
    client_name = serializers.CharField(source="client.get_full_name")
    client_phone = serializers.CharField(source="client.phone_number")
    producer_name = serializers.CharField(source="stock.producer.get_full_name")
    producer_phone = serializers.CharField(source="stock.producer.phone_number")


class DeliverySerializer(serializers.ModelSerializer):
    """Serializer complet pour une livraison."""
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    order_detail = OrderDetailSerializer(source="order", read_only=True)

    class Meta:
        model = Delivery
        fields = [
            "id",
            "status",
            "status_display",
            "delivery_fee",
            "order_detail",
            "pickup_time",
            "delivery_time",
            "created_at",
        ]


class DriverDeliveryListSerializer(DeliverySerializer):
    """Serializer pour la liste des livraisons (identique au complet pour le mobile)."""
    pass


class DeliveryUpdateSerializer(serializers.Serializer):
    """Serializer pour la mise à jour du statut par le livreur."""
    status = serializers.ChoiceField(choices=Delivery.Status.choices)
    otp_code = serializers.CharField(required=False, max_length=6)
