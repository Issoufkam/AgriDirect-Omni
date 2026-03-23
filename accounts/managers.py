"""
Manager personnalisé pour CustomUser.

Gère la création d'utilisateurs avec phone_number comme identifiant.
"""

from django.contrib.auth.models import BaseUserManager


class CustomUserManager(BaseUserManager):
    """
    Manager personnalisé qui utilise phone_number au lieu de username.
    """

    def create_user(self, phone_number, password=None, **extra_fields):
        """
        Crée et retourne un utilisateur standard.

        Args:
            phone_number: Numéro de téléphone unique.
            password: Mot de passe (optionnel pour auth SMS).
            **extra_fields: Champs supplémentaires du modèle.

        Raises:
            ValueError: Si phone_number n'est pas fourni.
        """
        if not phone_number:
            raise ValueError("Le numéro de téléphone est obligatoire.")

        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)

        user = self.model(phone_number=phone_number, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, phone_number, password=None, **extra_fields):
        """
        Crée et retourne un superutilisateur.

        Args:
            phone_number: Numéro de téléphone unique.
            password: Mot de passe (obligatoire pour le superuser).
            **extra_fields: Champs supplémentaires.

        Raises:
            ValueError: Si is_staff ou is_superuser sont False.
        """
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_verified", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Le superuser doit avoir is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Le superuser doit avoir is_superuser=True.")

        return self.create_user(phone_number, password, **extra_fields)
