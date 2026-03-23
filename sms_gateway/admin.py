"""
Configuration admin pour l'application SMS Gateway.
"""

from django.contrib import admin

from .models import SMSLog


@admin.register(SMSLog)
class SMSLogAdmin(admin.ModelAdmin):
    """Admin pour le modèle SMSLog."""

    list_display = [
        "id",
        "direction",
        "phone_number",
        "status",
        "raw_text_short",
        "user",
        "created_at",
    ]
    list_filter = ["direction", "status"]
    search_fields = ["phone_number", "raw_text"]
    readonly_fields = ["created_at", "parsed_data"]

    @admin.display(description="SMS (extrait)")
    def raw_text_short(self, obj):
        """Affiche les 60 premiers caractères du SMS."""
        return obj.raw_text[:60] + "..." if len(obj.raw_text) > 60 else obj.raw_text
