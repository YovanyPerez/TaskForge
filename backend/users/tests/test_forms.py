from django.test import TestCase

from users.forms import UserProfileForm, UserRegistrationForm
from users.models import User


class UserRegistrationFormTests(TestCase):
    def test_valid_registration(self):
        form = UserRegistrationForm(
            data={
                "username": "bob",
                "email": "bob@example.com",
                "password1": "Str0ngPass!",
                "password2": "Str0ngPass!",
            }
        )
        self.assertTrue(form.is_valid(), form.errors)

    def test_password_mismatch(self):
        form = UserRegistrationForm(
            data={
                "username": "bob",
                "email": "bob@example.com",
                "password1": "Str0ngPass!",
                "password2": "DifferentPass!",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("password2", form.errors)

    def test_email_required(self):
        form = UserRegistrationForm(
            data={
                "username": "bob",
                "password1": "Str0ngPass!",
                "password2": "Str0ngPass!",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)

    def test_password_without_special_character_rejected(self):
        for password in ("molimoli", "Molimoli1"):
            with self.subTest(password=password):
                form = UserRegistrationForm(
                    data={
                        "username": "bob",
                        "email": "bob@example.com",
                        "password1": password,
                        "password2": password,
                    }
                )
                self.assertFalse(form.is_valid())
                self.assertIn("password2", form.errors)

    def test_password_with_special_character_accepted(self):
        form = UserRegistrationForm(
            data={
                "username": "bob",
                "email": "bob@example.com",
                "password1": "Molimoli!1",
                "password2": "Molimoli!1",
            }
        )
        self.assertTrue(form.is_valid(), form.errors)

    def test_duplicate_username(self):
        User.objects.create_user(username="bob", password="pass12345")
        form = UserRegistrationForm(
            data={
                "username": "bob",
                "email": "bob2@example.com",
                "password1": "Str0ngPass!",
                "password2": "Str0ngPass!",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("username", form.errors)


class UserProfileFormTests(TestCase):
    def test_profile_form_valid(self):
        user = User.objects.create_user(username="alice", password="pass12345")
        form = UserProfileForm(
            data={
                "first_name": "Alice",
                "last_name": "Doe",
                "email": "alice@example.com",
            },
            instance=user,
        )
        self.assertTrue(form.is_valid(), form.errors)
