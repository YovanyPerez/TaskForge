from django.contrib.auth import views as auth_views
from django.urls import path

from . import views
from .forms import UserLoginForm

app_name = "users"

urlpatterns = [
    path(
        "login/",
        auth_views.LoginView.as_view(
            template_name="users/login.html",
            authentication_form=UserLoginForm,
        ),
        name="login",
    ),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("register/", views.RegisterView.as_view(), name="register"),
    path("profile/", views.ProfileUpdateView.as_view(), name="profile"),
    path("settings/", views.SettingsView.as_view(), name="settings"),
    path("switch-language/", views.switch_language, name="switch-language"),
    path("team/", views.TeamListView.as_view(), name="team-list"),
    path("team/<int:pk>/", views.TeamDetailView.as_view(), name="team-detail"),
]
