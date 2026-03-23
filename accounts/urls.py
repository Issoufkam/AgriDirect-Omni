"""
URLs pour l'application Accounts.
"""

from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("register/", views.RegisterView.as_view(), name="register"),
    path("profile/", views.ProfileView.as_view(), name="profile"),
    path(
        "driver/location/",
        views.UpdateDriverLocationView.as_view(),
        name="driver-location",
    ),
]
