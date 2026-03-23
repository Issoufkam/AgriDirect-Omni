from django.urls import path
from .views import (
    DeliveryUpdateView, 
    DeliveryDetailView, 
    DriverDeliveryListView,
    DeliveryUIView
)

app_name = "deliveries"

urlpatterns = [
    # UI Livreur (PWA/Mobile optimized)
    path("livraisons/", DeliveryUIView.as_view(), name="delivery_ui"),
    
    # API Livraisons
    path("api/deliveries/", DriverDeliveryListView.as_view(), name="delivery_list"),
    path("api/deliveries/<int:pk>/", DeliveryUpdateView.as_view(), name="delivery_update"),
    path("api/deliveries-detail/<int:pk>/", DeliveryDetailView.as_view(), name="delivery_detail"),
]
