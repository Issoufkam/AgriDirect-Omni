from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from .models import Product, Stock

User = get_user_model()

class StockPublicationTests(APITestCase):
    """
    Tests du flux de publication de stocks par les producteurs.
    """

    def setUp(self):
        # Création d'un produit global
        self.product = Product.objects.create(
            name="Maïs Jaune",
            category="VIVRIER",
            unit="KG",
            national_price=250
        )
        
        # Création d'un producteur
        self.producer = User.objects.create_user(
            phone_number="+2250101010101",
            first_name="Jean",
            last_name="Dupont",
            password="password123",
            role="PRODUCTEUR"
        )
        
        # Création d'un client
        self.client_user = User.objects.create_user(
            phone_number="+2250202020202",
            first_name="Marie",
            last_name="Koffi",
            password="password123",
            role="CLIENT"
        )
        
        self.stock_url = reverse('products:stock-create')
        self.marketplace_url = reverse('products:marketplace_api')

    def test_publish_stock_success(self):
        """Un producteur peut publier un stock valide."""
        self.client.force_authenticate(user=self.producer)
        data = {
            "product": self.product.id,
            "quantity": 500,
            "remaining_quantity": 500,
            "location_lat": 5.348,
            "location_lng": -4.030,
            "needs_refrigeration": False
        }
        response = self.client.post(self.stock_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Stock.objects.count(), 1)
        
        stock = Stock.objects.first()
        self.assertEqual(stock.producer, self.producer)
        self.assertEqual(stock.product, self.product)

    def test_publish_stock_unauthorized_client(self):
        """Un client ne doit pas pouvoir publier de stock."""
        self.client.force_authenticate(user=self.client_user)
        data = {
            "product": self.product.id,
            "quantity": 500,
            "remaining_quantity": 500,
            "location_lat": 5.348,
            "location_lng": -4.030
        }
        response = self.client.post(self.stock_url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_marketplace_listing(self):
        """Vérifier que le stock publié apparaît dans la marketplace."""
        # Publier un stock
        Stock.objects.create(
            producer=self.producer,
            product=self.product,
            quantity=100,
            remaining_quantity=100,
            location_lat=5.348,
            location_lng=-4.030
        )
        
        # Consulter la marketplace (API publique)
        response = self.client.get(self.marketplace_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['product']['name'], "Maïs Jaune")

    def test_stock_unit_price_calculation(self):
        """Vérifier que le prix unitaire tient compte de la remise dynamique."""
        stock = Stock.objects.create(
            producer=self.producer,
            product=self.product,
            quantity=100,
            remaining_quantity=100,
            location_lat=5.348,
            location_lng=-4.030,
            dynamic_discount=0.10 # 10%
        )
        # 250 - 10% = 225
        self.assertEqual(stock.unit_price, 225)
