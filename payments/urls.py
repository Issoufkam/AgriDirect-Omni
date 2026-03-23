from django.urls import path
from .views import InitializePaymentView, MobileMoneyWebhookView

app_name = "payments"

urlpatterns = [
    path("orders/<int:pk>/pay/", InitializePaymentView.as_view(), name="initialize_payment"),
    path("webhook/mobilemoney/", MobileMoneyWebhookView.as_view(), name="webhook_mobile_money"),
]
