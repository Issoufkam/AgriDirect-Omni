"""
Vues API pour l'application Products.

Fournit l'endpoint marketplace avec recherche géolocalisée.
"""

from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from django.views.generic import TemplateView
from .models import Product, Stock
from .serializers import MarketplaceItemSerializer, ProductSerializer, StockSerializer
from .services import get_marketplace_stocks


class MarketplaceView(APIView):
    """
    GET /api/marketplace/

    Liste des produits disponibles sur la marketplace,
    triés par proximité si la position du client est fournie.

    Query Parameters:
        lat (float): Latitude du client.
        lng (float): Longitude du client.
        radius (float): Rayon de recherche en km (optionnel).
        category (str): Filtre par catégorie (VIVRIER, CARNE, HALIEUTIQUE, ELEVAGE).
        product (str): Recherche par nom de produit.
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """
        Retourne la liste des stocks disponibles.

        Les résultats incluent les informations du produit, du producteur,
        la quantité disponible et la distance par rapport au client.
        """
        # Extraction des paramètres de requête
        lat = request.query_params.get("lat")
        lng = request.query_params.get("lng")
        radius = request.query_params.get("radius")
        category = request.query_params.get("category")
        product_name = request.query_params.get("product")

        # Conversion des coordonnées
        latitude = float(lat) if lat else None
        longitude = float(lng) if lng else None
        radius_km = float(radius) if radius else None

        # Appel du service métier
        stocks = get_marketplace_stocks(
            latitude=latitude,
            longitude=longitude,
            radius_km=radius_km,
            category=category,
            product_name=product_name,
        )

        serializer = MarketplaceItemSerializer(stocks, many=True)
        return Response(
            {
                "count": len(stocks),
                "results": serializer.data,
            },
            status=status.HTTP_200_OK,
        )


class MarketplaceUIView(TemplateView):
    """
    Vue pour afficher l'interface graphique de la Marketplace (Boutique Client).
    """
    template_name = "products/marketplace.html"


class ProductPriceListView(generics.ListAPIView):
    """
    GET /api/products/prices/
    Liste les prix nationaux conseillés pour tous les produits actifs.
    """
    queryset = Product.objects.filter(is_active=True)
    serializer_class = ProductSerializer
    permission_classes = [permissions.AllowAny]


class StockCreateView(generics.CreateAPIView):
    """
    POST /api/stocks/
    Permet à un producteur de publier un nouveau stock.
    """
    serializer_class = StockSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        # On force le producteur à être l'utilisateur connecté
        serializer.save(producer=self.request.user)
