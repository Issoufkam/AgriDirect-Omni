"""
URLs pour l'application Orders.
"""

from django.urls import path

from . import views

app_name = "orders"

urlpatterns = [
    path("api/orders/", views.OrderCreateView.as_view(), name="order-create"),
    path("api/orders/list/", views.OrderListView.as_view(), name="order-list"),
    path("api/orders/<int:pk>/cancel/", views.OrderCancelView.as_view(), name="order-cancel"),
    path("api/producer/orders/", views.ProducerOrderListView.as_view(), name="producer-orders"),
    
    # UI Historique (Client)
    path("mes-commandes/", views.OrderHistoryUIView.as_view(), name="order_history_ui"),
]
