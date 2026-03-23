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
    
    # API Auth (JWT endpoints should be CSRF exempt if called via AJAX without session)
    path("api/login/", csrf_exempt(TokenObtainPairView.as_view()), name="token_obtain_pair"),
    path("api/token/refresh/", csrf_exempt(TokenRefreshView.as_view()), name="token_refresh"),
    
    path("api/register/", csrf_exempt(views.RegisterView.as_view()), name="register"),
    path("api/profile/", views.ProfileView.as_view(), name="profile"),
    path(
        "driver/location/",
        views.UpdateDriverLocationView.as_view(),
        name="driver-location",
    ),
]
