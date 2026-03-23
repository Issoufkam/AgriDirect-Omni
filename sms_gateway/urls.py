"""
URLs pour l'application SMS Gateway.
"""

from django.urls import path

from . import views

app_name = "sms_gateway"

urlpatterns = [
    path("sms-webhook/", views.SMSWebhookView.as_view(), name="sms-webhook"),
]
