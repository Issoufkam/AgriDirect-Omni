"""
Configuration admin pour l'application Accounts.
"""

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin

User = get_user_model()


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """Admin personnalisé pour CustomUser."""

    model = User
    list_display = [
        "phone_number",
        "first_name",
        "last_name",
        "role",
        "sub_role",
        "is_verified",
        "is_active",
    ]
    list_filter = ["role", "sub_role", "is_verified", "is_active_driver"]
    search_fields = ["phone_number", "first_name", "last_name"]
    ordering = ["-date_joined"]

    fieldsets = (
        (None, {"fields": ("phone_number", "password")}),
        ("Informations personnelles", {"fields": ("first_name", "last_name", "avatar")}),
        ("Rôles", {"fields": ("role", "sub_role")}),
        (
            "Livreur",
            {
                "fields": (
                    "is_active_driver",
                    "has_refrigeration",
                    "current_location_lat",
                    "current_location_lng",
                ),
            },
        ),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "is_verified",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        ("Dates", {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "phone_number",
                    "first_name",
                    "last_name",
                    "role",
                    "password1",
                    "password2",
                ),
            },
        ),
    )
