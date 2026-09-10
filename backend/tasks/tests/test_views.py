from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from projects.models import Project
from tasks.models import Task
from users.models import Role

User = get_user_model()


class TaskCrudTests(TestCase):
    def setUp(self):
        self.manager = User.objects.create_user(
            username="mg", role=Role.MANAGER, password="pass12345"
        )
        self.member = User.objects.create_user(
            username="mb", role=Role.MEMBER, password="pass12345"
        )
        self.project = Project.objects.create(name="Alpha", created_by=self.manager)
        self.project.members.add(self.manager, self.member)

    def _create_task(self):
        return Task.objects.create(
            title="Do thing", project=self.project, created_by=self.manager
        )

    def test_list_requires_login(self):
        response = self.client.get(reverse("tasks:list", args=[self.project.pk]))
        self.assertEqual(response.status_code, 302)

    def test_list(self):
        self.client.force_login(self.member)
        self._create_task()
        response = self.client.get(reverse("tasks:list", args=[self.project.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Do thing")

    def test_create_requires_manager(self):
        self.client.force_login(self.member)
        response = self.client.get(reverse("tasks:create", args=[self.project.pk]))
        self.assertEqual(response.status_code, 403)

    def test_create_with_assignment(self):
        self.client.force_login(self.manager)
        response = self.client.post(
            reverse("tasks:create", args=[self.project.pk]),
            {
                "title": "Do thing",
                "description": "Details",
                "assigned_to": self.member.pk,
                "priority": "HIGH",
                "status": "TODO",
                "due_date": "2026-06-01",
            },
        )
        self.assertRedirects(response, reverse("tasks:list", args=[self.project.pk]))
        task = Task.objects.get(title="Do thing")
        self.assertEqual(task.project, self.project)
        self.assertEqual(task.created_by, self.manager)
        self.assertEqual(task.assigned_to, self.member)

    def test_update(self):
        self.client.force_login(self.manager)
        task = self._create_task()
        response = self.client.post(
            reverse("tasks:update", args=[self.project.pk, task.pk]),
            {"title": "Do thing v2", "priority": "LOW", "status": "DONE"},
        )
        self.assertRedirects(response, reverse("tasks:list", args=[self.project.pk]))
        task.refresh_from_db()
        self.assertEqual(task.title, "Do thing v2")
        self.assertEqual(task.status, "DONE")

    def test_delete(self):
        self.client.force_login(self.manager)
        task = self._create_task()
        response = self.client.post(
            reverse("tasks:delete", args=[self.project.pk, task.pk])
        )
        self.assertRedirects(response, reverse("tasks:list", args=[self.project.pk]))
        self.assertFalse(Task.objects.filter(pk=task.pk).exists())

    def test_delete_requires_manager(self):
        self.client.force_login(self.member)
        task = self._create_task()
        response = self.client.post(
            reverse("tasks:delete", args=[self.project.pk, task.pk])
        )
        self.assertEqual(response.status_code, 403)
        self.assertTrue(Task.objects.filter(pk=task.pk).exists())
