from django.template import loader
from django.test import TestCase


class ErrorPageTests(TestCase):
    def test_favicon_redirects_to_static(self):
        response = self.client.get("/favicon.ico")
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response.url, "/static/images/favicon.png")

    def test_404_uses_custom_template(self):
        response = self.client.get("/definitely-not-a-page/")
        self.assertEqual(response.status_code, 404)
        self.assertTemplateUsed(response, "404.html")

    def test_error_templates_load(self):
        for name in ("403.html", "500.html"):
            self.assertIsNotNone(loader.get_template(name))
