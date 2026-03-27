from django.urls import path
from . import views

app_name = "products"

urlpatterns = [
    # UI Marketplace (Public/Client)
    path("marketplace/", views.MarketplaceUIView.as_view(), name="marketplace_ui"),
    
    # API Marketplace
    path("api/marketplace/", views.MarketplaceView.as_view(), name="marketplace_api"),
    path("api/products/prices/", views.ProductPriceListView.as_view(), name="product-prices"),
    path("api/stocks/", views.StockCreateView.as_view(), name="stock-create"),
    path("api/producer/stocks/", views.StockListView.as_view(), name="producer-stocks-list"),
    path("api/stocks/<int:pk>/", views.StockDetailView.as_view(), name="stock-detail"),
]
