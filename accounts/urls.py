from django.urls import path
from django.views.generic import TemplateView
from django.views.decorators.csrf import csrf_exempt
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from . import views

app_name = "accounts"

urlpatterns = [
    # UI Auth
    path("login/", TemplateView.as_view(template_name="accounts/login.html"), name="login_ui"),
    path("signup/", TemplateView.as_view(template_name="accounts/signup.html"), name="signup_ui"),
    path("profile/", views.ProfileUIView.as_view(), name="profile_ui"),
    
    # API Auth (SimpleJWT)
    path("api/login/", csrf_exempt(TokenObtainPairView.as_view()), name="token_obtain_pair"),
    path("api/auth/token/", csrf_exempt(TokenObtainPairView.as_view()), name="token_obtain_pair_mobile"),
    path("api/token/refresh/", csrf_exempt(TokenRefreshView.as_view()), name="token_refresh"),
    path("api/auth/token/refresh/", csrf_exempt(TokenRefreshView.as_view()), name="token_refresh_mobile"),
    
    path("api/register/", csrf_exempt(views.RegisterView.as_view()), name="register"),
    path("api/auth/register/", csrf_exempt(views.RegisterView.as_view()), name="register_mobile"),
    
    path("api/profile/", views.ProfileView.as_view(), name="profile"),
    path("api/wallet/", views.WalletView.as_view(), name="wallet-api"),
    path("api/wallet/recharge/", views.WalletDepositView.as_view(), name="wallet-recharge"),
    path("api/wallet/withdraw/", views.WalletWithdrawView.as_view(), name="wallet-withdraw"),
    path("api/user/wallet/", views.WalletView.as_view(), name="wallet-api-mobile"),
    path("api/user/push-token/", views.UpdatePushTokenView.as_view(), name="push-token-mobile"),
    path(
        "driver/location/",
        views.UpdateDriverLocationView.as_view(),
        name="driver-location",
    ),
]
