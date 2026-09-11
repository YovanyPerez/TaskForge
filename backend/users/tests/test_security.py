from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

User = get_user_model()


class RegistrationApprovalTests(TestCase):
    def test_registered_user_is_inactive_and_cannot_login(self):
        response = self.client.post(
            reverse("users:register"),
            {
                "username": "bob",
                "email": "bob@example.com",
                "first_name": "Bob",
                "last_name": "Builder",
                "password1": "Str0ngPass!",
                "password2": "Str0ngPass!",
            },
        )
        self.assertRedirects(response, reverse("users:login"))
        self.assertFalse(User.objects.get(username="bob").is_active)

        response = self.client.post(
            reverse("users:login"),
            {"username": "bob", "password": "Str0ngPass!"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_approved_user_can_login(self):
        user = User.objects.create_user(
            username="carol", password="Str0ngPass!", is_active=False
        )
        user.is_active = True
        user.save(update_fields=["is_active"])

        response = self.client.post(
            reverse("users:login"),
            {"username": "carol", "password": "Str0ngPass!"},
        )
        self.assertRedirects(response, reverse("home"))


@override_settings(
    AXES_ENABLED=True,
    AXES_FAILURE_LIMIT=3,
    AXES_COOLOFF_TIME=timedelta(minutes=5),
    AXES_LOCKOUT_PARAMETERS=[["username", "ip_address"]],
)
class LockoutTests(TestCase):
    def test_lockout_after_repeated_failures(self):
        User.objects.create_user(username="dave", password="Correct123!")
        for _ in range(2):
            response = self.client.post(
                reverse("users:login"),
                {"username": "dave", "password": "wrong"},
            )
            self.assertEqual(response.status_code, 200)

        # Third failure reaches the limit and locks the account/IP.
        response = self.client.post(
            reverse("users:login"),
            {"username": "dave", "password": "wrong"},
        )
        self.assertEqual(response.status_code, 429)

        # While locked, even the right password is blocked.
        response = self.client.post(
            reverse("users:login"),
            {"username": "dave", "password": "Correct123!"},
        )
        self.assertEqual(response.status_code, 429)
