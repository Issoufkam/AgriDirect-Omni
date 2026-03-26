from rest_framework import permissions

class IsProducteur(permissions.BasePermission):
    """
    Permission permettant uniquement aux utilisateurs ayant le rôle PRODUCTEUR d'accéder.
    """
    def has_permission(self, request, view):
        return bool(
            request.user and 
            request.user.is_authenticated and 
            request.user.role == "PRODUCTEUR" # ou utiliser request.user.is_producteur si défini
        )
