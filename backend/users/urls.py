from django.contrib.auth import views as auth_views
from django.urls import path, reverse_lazy

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
    path(
        "password_reset/",
        auth_views.PasswordResetView.as_view(
            template_name="users/password_reset_form.html",
            email_template_name="users/password_reset_email.html",
            subject_template_name="users/password_reset_subject.txt",
            success_url=reverse_lazy("users:password_reset_done"),
        ),
        name="password_reset",
    ),
    path(
        "password_reset/done/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="users/password_reset_done.html",
        ),
        name="password_reset_done",
    ),
    path(
        "reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="users/password_reset_confirm.html",
            success_url=reverse_lazy("users:password_reset_complete"),
        ),
        name="password_reset_confirm",
    ),
    path(
        "reset/done/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="users/password_reset_complete.html",
        ),
        name="password_reset_complete",
    ),
    path("register/", views.RegisterView.as_view(), name="register"),
    path("profile/", views.ProfileUpdateView.as_view(), name="profile"),
    path("settings/", views.SettingsView.as_view(), name="settings"),
    path("switch-language/", views.switch_language, name="switch-language"),
    path("team/", views.TeamListView.as_view(), name="team-list"),
    path("team/<int:pk>/", views.TeamDetailView.as_view(), name="team-detail"),
]
