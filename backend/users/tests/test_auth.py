from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from users.models import Role

User = get_user_model()


class RegistrationTests(TestCase):
    def test_register_view_get(self):
        response = self.client.get(reverse("users:register"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "users/register.html")

    def test_register_creates_member(self):
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
        user = User.objects.get(username="bob")
        self.assertEqual(user.role, Role.MEMBER)
        self.assertEqual(user.email, "bob@example.com")


class LoginLogoutTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="alice", password="pass12345")

    def test_login_success(self):
        response = self.client.post(
            reverse("users:login"),
            {"username": "alice", "password": "pass12345"},
        )
        self.assertRedirects(response, reverse("home"))
        self.assertEqual(int(self.client.session["_auth_user_id"]), self.user.pk)

    def test_login_bad_credentials(self):
        response = self.client.post(
            reverse("users:login"),
            {"username": "alice", "password": "wrong"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["user"].is_authenticated)

    def test_logout(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse("users:logout"))
        self.assertRedirects(response, reverse("home"))
        self.assertNotIn("_auth_user_id", self.client.session)


class ProfileTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="alice", password="pass12345")

    def test_profile_requires_login(self):
        response = self.client.get(reverse("users:profile"))
        self.assertRedirects(response, f"{reverse('users:login')}?next={reverse('users:profile')}")

    def test_profile_update(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("users:profile"),
            {"first_name": "Alice", "last_name": "Doe", "email": "alice@example.com"},
        )
        self.assertRedirects(response, reverse("users:profile"))
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "Alice")
        self.assertEqual(self.user.email, "alice@example.com")


class RoleHelperTests(TestCase):
    def test_role_helpers(self):
        admin = User.objects.create_user(username="a", role=Role.ADMIN, password="pass12345")
        manager = User.objects.create_user(username="m", role=Role.MANAGER, password="pass12345")
        member = User.objects.create_user(username="u", role=Role.MEMBER, password="pass12345")

        self.assertTrue(admin.is_admin)
        self.assertTrue(manager.is_manager)
        self.assertTrue(member.role == Role.MEMBER)
        self.assertFalse(member.is_admin)
        self.assertFalse(manager.is_admin)
