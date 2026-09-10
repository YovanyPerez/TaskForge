from django.test import TestCase

from projects.forms import ProjectForm


class ProjectFormTests(TestCase):
    def test_end_date_before_start_date_invalid(self):
        form = ProjectForm(
            data={
                "name": "Alpha",
                "status": "PLANNING",
                "start_date": "2026-09-09",
                "end_date": "2026-09-03",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("end_date", form.errors)

    def test_valid_dates(self):
        form = ProjectForm(
            data={
                "name": "Alpha",
                "status": "PLANNING",
                "start_date": "2026-09-03",
                "end_date": "2026-09-09",
            }
        )
        self.assertTrue(form.is_valid(), form.errors)

    def test_empty_dates_valid(self):
        form = ProjectForm(data={"name": "Alpha", "status": "PLANNING"})
        self.assertTrue(form.is_valid(), form.errors)
