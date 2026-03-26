from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from accounts.models import Wallet

User = get_user_model()

class AuthenticationTests(APITestCase):
    """
    Tests de l'authentification (Inscription, Connexion, JWT).
    """

    def setUp(self):
        self.register_url = reverse('accounts:register')
        self.login_url = reverse('accounts:token_obtain_pair')
        self.profile_url = reverse('accounts:profile')
        
        self.user_data = {
            "phone_number": "+2250102030405",
            "first_name": "Test",
            "last_name": "User",
            "password": "testpassword123",
            "role": "CLIENT"
        }

    def test_registration_success(self):
        """Tester l'inscription d'un nouvel utilisateur."""
        response = self.client.post(self.register_url, self.user_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 1)
        
        user = User.objects.get(phone_number="+2250102030405")
        self.assertEqual(user.first_name, "Test")
        self.assertEqual(user.role, "CLIENT")
        
        # Vérifier que le portefeuille a été créé automatiquement
        self.assertTrue(Wallet.objects.filter(user=user).exists())

    def test_registration_duplicate_phone(self):
        """Tester que l'on ne peut pas s'inscrire deux fois avec le même numéro."""
        User.objects.create_user(**self.user_data)
        response = self.client.post(self.register_url, self.user_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("phone_number", response.data)

    def test_login_success(self):
        """Tester la connexion et la récupération des tokens JWT."""
        User.objects.create_user(**self.user_data)
        
        login_data = {
            "phone_number": "+2250102030405",
            "password": "testpassword123"
        }
        response = self.client.post(self.login_url, login_data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_login_invalid_credentials(self):
        """Tester la connexion avec de mauvais identifiants."""
        User.objects.create_user(**self.user_data)
        
        login_data = {
            "phone_number": "+2250102030405",
            "password": "wrongpassword"
        }
        response = self.client.post(self.login_url, login_data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_profile_access_with_jwt(self):
        """Tester l'accès au profil avec un token JWT valide."""
        user = User.objects.create_user(**self.user_data)
        
        # Obtenir le token
        login_response = self.client.post(self.login_url, {
            "phone_number": self.user_data["phone_number"],
            "password": self.user_data["password"]
        })
        token = login_response.data["access"]
        
        # Accéder au profil
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.get(self.profile_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["phone_number"], user.phone_number)

    def test_profile_access_unauthorized(self):
        """Tester que l'accès au profil est bloqué sans authentification."""
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
