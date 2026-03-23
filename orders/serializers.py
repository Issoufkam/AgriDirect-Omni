"""
Serializers pour l'application Orders.
"""

from rest_framework import serializers

from products.serializers import ProductSerializer
from .models import Order


class OrderCreateSerializer(serializers.Serializer):
    """
    Serializer pour la création de commande.

    Valide les données d'entrée et délègue la création au service métier.
    Le prix est calculé automatiquement à partir du national_price.
    """

    stock_id = serializers.IntegerField(
        help_text="ID du stock à commander."
    )
    quantity = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Quantité souhaitée."
    )
    delivery_address = serializers.CharField(
        help_text="Adresse de livraison textuelle."
    )
    client_lat = serializers.FloatField(
        help_text="Latitude du client."
    )
    client_lng = serializers.FloatField(
        help_text="Longitude du client."
    )


class OrderSerializer(serializers.ModelSerializer):
    """
    Serializer complet pour une commande (lecture).
    """

    client_name = serializers.CharField(source="client.get_full_name", read_only=True)
    client_phone = serializers.CharField(source="client.phone_number", read_only=True)
    producer_name = serializers.CharField(
        source="stock.producer.get_full_name", read_only=True
    )
    producer_phone = serializers.CharField(
        source="stock.producer.phone_number", read_only=True
    )
    product_name = serializers.CharField(source="stock.product.name", read_only=True)
    product_unit = serializers.CharField(
        source="stock.product.get_unit_display", read_only=True
    )
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    payment_status_display = serializers.CharField(
        source="get_payment_status_display", read_only=True
    )
    product_image = serializers.SerializerMethodField()

    def get_product_image(self, obj):
        if obj.stock.product.image:
            return obj.stock.product.image.url
        return None

    class Meta:
        model = Order
        fields = [
            "id",
            "client_name",
            "client_phone",
            "producer_name",
            "producer_phone",
            "product_name",
            "product_unit",
            "product_image",
            "quantity",
            "unit_price",
            "total_product_amount",
            "delivery_fee",
            "total_amount",
            "status",
            "status_display",
            "payment_status",
            "payment_status_display",
            "transaction_id",
            "payment_provider",
            "delivery_address",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields
