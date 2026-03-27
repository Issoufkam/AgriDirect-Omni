"""
Serializers pour l'application Products.

Sérialise les produits et stocks pour l'API marketplace.
"""

from rest_framework import serializers

from .models import Product, Stock


class ProductSerializer(serializers.ModelSerializer):
    """
    Serializer pour le modèle Product.
    """

    unit_display = serializers.CharField(source="get_unit_display", read_only=True)
    category_display = serializers.CharField(source="get_category_display", read_only=True)

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "category",
            "category_display",
            "unit",
            "unit_display",
            "national_price",
            "needs_refrigeration",
            "image",
            "is_active",
        ]
        read_only_fields = ["id"]


class ProducerSerializer(serializers.Serializer):
    full_name = serializers.CharField()
    phone = serializers.CharField()
    average_rating = serializers.FloatField(read_only=True)


class MarketplaceItemProductSerializer(serializers.Serializer):
    name = serializers.CharField()
    category_display = serializers.CharField()
    unit = serializers.CharField()
    original_price = serializers.DecimalField(max_digits=10, decimal_places=0)
    unit_price = serializers.DecimalField(max_digits=10, decimal_places=0)
    image = serializers.CharField(allow_null=True)


class MarketplaceItemSerializer(serializers.Serializer):
    """
    Serializer pour les résultats de la marketplace (structure imbriquée).
    """
    id = serializers.IntegerField()
    product = MarketplaceItemProductSerializer()
    remaining_quantity = serializers.DecimalField(max_digits=10, decimal_places=2)
    producer = ProducerSerializer()
    needs_refrigeration = serializers.BooleanField()
    distance_km = serializers.FloatField(allow_null=True)
    location_lat = serializers.FloatField()
    location_lng = serializers.FloatField()


class StockSerializer(serializers.ModelSerializer):
    """
    Serializer pour le modèle Stock.
    """
    product_detail = ProductSerializer(source="product", read_only=True)
    producer_name = serializers.CharField(source="producer.get_full_name", read_only=True)
    producer_phone = serializers.CharField(source="producer.phone_number", read_only=True)
    image = serializers.ImageField(required=False, allow_null=True)
    description = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    price_override = serializers.DecimalField(max_digits=10, decimal_places=0, required=False, allow_null=True)

    class Meta:
        model = Stock
        fields = [
            "id",
            "producer_name",
            "producer_phone",
            "product",
            "product_detail",
            "quantity",
            "unit",
            "remaining_quantity",
            "reserved_quantity",
            "available_quantity",
            "variety",
            "grade",
            "description",
            "price_override",
            "image",
            "location_lat",
            "location_lng",
            "needs_refrigeration",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def validate_price_override(self, value):
        """Permet de convertir une chaîne vide en None."""
        if value == "":
            return None
        return value

    def validate(self, data):
        """Vérifie que le prix personnalisé ne dépasse pas le prix de référence national."""
        product = data.get("product")
        price_override = data.get("price_override")

        if product and price_override:
            # S'assurer que price_override est un Decimal pour la comparaison
            from decimal import Decimal
            price_override = Decimal(str(price_override))
            if price_override > product.national_price:
                raise serializers.ValidationError(
                    {"price_override": f"Le prix ne peut pas dépasser le prix de référence national ({product.national_price} FCFA)."}
                )
        return data
