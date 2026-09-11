import re

from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse

User = get_user_model()


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class PasswordResetFlowTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="alice", email="alice@example.com", password="OldPass123!"
        )

    def test_reset_form_get(self):
        response = self.client.get(reverse("users:password_reset"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "users/password_reset_form.html")

    def test_unknown_email_sends_nothing_but_does_not_leak(self):
        response = self.client.post(
            reverse("users:password_reset"), {"email": "nobody@example.com"}
        )
        self.assertRedirects(response, reverse("users:password_reset_done"))
        self.assertEqual(len(mail.outbox), 0)

    def test_full_reset_flow_sets_new_password(self):
        response = self.client.post(
            reverse("users:password_reset"), {"email": "alice@example.com"}
        )
        self.assertRedirects(response, reverse("users:password_reset_done"))
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("alice@example.com", mail.outbox[0].to)

        match = re.search(r"/accounts/reset/([^/]+)/([^/]+)/", mail.outbox[0].body)
        self.assertIsNotNone(match, "reset link missing from email body")
        uidb64, token = match.groups()

        confirm_url = reverse(
            "users:password_reset_confirm", kwargs={"uidb64": uidb64, "token": token}
        )
        response = self.client.get(confirm_url, follow=True)
        self.assertTrue(response.context["validlink"])

        response = self.client.post(
            response.redirect_chain[-1][0],
            {"new_password1": "NewPass456!", "new_password2": "NewPass456!"},
        )
        self.assertRedirects(response, reverse("users:password_reset_complete"))

        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("NewPass456!"))
