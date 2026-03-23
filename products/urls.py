from django.urls import path
from .views import MarketplaceView, MarketplaceUIView

app_name = "products"

urlpatterns = [
    # UI Marketplace (Public/Client)
    path("marketplace/", MarketplaceUIView.as_view(), name="marketplace_ui"),
    
    # API Marketplace
    path("api/marketplace/", MarketplaceView.as_view(), name="marketplace_api"),
]
