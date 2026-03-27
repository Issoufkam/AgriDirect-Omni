"""
Configuration admin pour l'application Deliveries.
"""

from django.contrib import admin

from .models import Delivery


@admin.register(Delivery)
class DeliveryAdmin(admin.ModelAdmin):
    """Admin pour le modèle Delivery."""

    list_display = [
        "id",
        "order",
        "driver",
        "status",
        "delivery_fee",
        "pickup_time",
        "delivery_time",
        "created_at",
    ]
    list_filter = ["status"]
    search_fields = ["driver__phone_number", "pickup_otp", "delivery_otp"]
    raw_id_fields = ["order", "driver"]
    readonly_fields = ["pickup_otp", "delivery_otp", "created_at", "updated_at"]
