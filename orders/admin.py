"""
Configuration admin pour l'application Orders.
"""

from django.contrib import admin

from .models import Order


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """Admin pour le modèle Order."""

    list_display = [
        "id",
        "client",
        "status",
        "total_amount",
        "payment_status",
        "delivery_fee",
        "created_at",
    ]
    list_filter = ["status", "payment_status", "payment_provider"]
    search_fields = ["client__phone_number", "transaction_id"]
    raw_id_fields = ["client", "stock"]
    readonly_fields = ["created_at", "updated_at"]
