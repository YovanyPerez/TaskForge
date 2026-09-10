from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

User = get_user_model()


class SettingsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="alice", password="pass12345")

    def test_settings_requires_login(self):
        response = self.client.get(reverse("users:settings"))
        self.assertEqual(response.status_code, 302)

    def test_change_language(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse("users:settings"), {"language": "es"})
        self.assertRedirects(response, reverse("users:settings"))
        self.user.refresh_from_db()
        self.assertEqual(self.user.language, "es")

    def test_invalid_language_rejected(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse("users:settings"), {"language": "xx"})
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.language, "")

    def test_dashboard_in_spanish(self):
        self.user.language = "es"
        self.user.save()
        self.client.force_login(self.user)
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Proyectos")
        self.assertContains(response, "Buenos días")

    def test_dashboard_in_english_by_default(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Projects")

    def test_settings_page_has_appearance_options(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("users:settings"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "data-tf-accent-option")
        self.assertContains(response, "data-tf-density-option")

    def test_switch_language_anonymous_uses_cookie(self):
        response = self.client.post(
            reverse("users:switch-language"), {"language": "es", "next": "/"}
        )
        self.assertRedirects(response, "/")
        self.assertEqual(response.cookies["django_language"].value, "es")
        response = self.client.get(reverse("home"))
        self.assertContains(response, 'lang="es"')
        self.assertContains(response, "Iniciar sesión")

    def test_switch_language_authenticated_saves_profile(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("users:switch-language"), {"language": "es", "next": "/"}
        )
        self.assertRedirects(response, "/")
        self.user.refresh_from_db()
        self.assertEqual(self.user.language, "es")

    def test_switch_language_invalid_falls_back_to_english(self):
        response = self.client.post(
            reverse("users:switch-language"), {"language": "xx", "next": "/"}
        )
        self.assertRedirects(response, "/")
        self.assertEqual(response.cookies["django_language"].value, "en")

    def test_register_form_labels_in_spanish(self):
        self.user.language = "es"
        self.user.save()
        self.client.force_login(self.user)
        response = self.client.get(reverse("users:register"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Correo electrónico")
        self.assertContains(response, "Nombre de usuario")
        self.assertNotContains(response, ">Email<")
