from django.test import TestCase

from projects.models import Project
from tasks.forms import TaskForm
from users.models import User


class TaskFormTests(TestCase):
    def setUp(self):
        self.manager = User.objects.create_user(username="mg", password="pass12345")
        self.member = User.objects.create_user(username="mb", password="pass12345")
        self.outsider = User.objects.create_user(username="out", password="pass12345")
        self.project = Project.objects.create(name="Alpha", created_by=self.manager)
        self.project.members.add(self.manager, self.member)

    def test_assign_to_member_is_valid(self):
        form = TaskForm(
            data={
                "title": "T1",
                "assigned_to": self.member.pk,
                "priority": "LOW",
                "status": "TODO",
            },
            project=self.project,
        )
        self.assertTrue(form.is_valid(), form.errors)

    def test_assign_to_non_member_invalid(self):
        form = TaskForm(
            data={
                "title": "T1",
                "assigned_to": self.outsider.pk,
                "priority": "LOW",
                "status": "TODO",
            },
            project=self.project,
        )
        self.assertFalse(form.is_valid())
        self.assertIn("assigned_to", form.errors)
