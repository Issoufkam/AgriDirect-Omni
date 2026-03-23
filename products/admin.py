"""
Configuration admin pour l'application Products.
"""

from django.contrib import admin

from .models import Product, Stock


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """Admin pour le modèle Product."""

    list_display = [
        "name",
        "category",
        "unit",
        "national_price",
        "needs_refrigeration",
        "is_active",
    ]
    list_filter = ["category", "unit", "needs_refrigeration", "is_active"]
    search_fields = ["name"]
    list_editable = ["national_price", "is_active"]


@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    """Admin pour le modèle Stock."""

    list_display = [
        "producer",
        "product",
        "quantity",
        "remaining_quantity",
        "needs_refrigeration",
        "created_at",
    ]
    list_filter = ["product__category", "needs_refrigeration"]
    search_fields = ["producer__phone_number", "product__name"]
    raw_id_fields = ["producer", "product"]
