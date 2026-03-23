"""
URLs pour l'application Accounts.
"""

from django.urls import path

from . import views
from django.views.generic import TemplateView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

app_name = "accounts"

urlpatterns = [
    # UI Auth
    path("login/", TemplateView.as_view(template_name="accounts/login.html"), name="login_ui"),
    path("signup/", TemplateView.as_view(template_name="accounts/signup.html"), name="signup_ui"),
    
    # API Auth
    path("api/login/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    
    path("api/register/", views.RegisterView.as_view(), name="register"),
    path("api/profile/", views.ProfileView.as_view(), name="profile"),
    path(
        "driver/location/",
        views.UpdateDriverLocationView.as_view(),
        name="driver-location",
    ),
]
