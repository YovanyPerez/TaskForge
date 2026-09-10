from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from projects.models import Project
from tasks.models import Task, TaskStatus
from users.models import Role

User = get_user_model()


class TaskStatusUpdateTests(TestCase):
    def setUp(self):
        self.manager = User.objects.create_user(
            username="mg", role=Role.MANAGER, password="pass12345"
        )
        self.assignee = User.objects.create_user(
            username="as", role=Role.MEMBER, password="pass12345"
        )
        self.other = User.objects.create_user(
            username="ot", role=Role.MEMBER, password="pass12345"
        )
        self.project = Project.objects.create(name="Alpha", created_by=self.manager)
        self.project.members.add(self.assignee, self.other)
        self.task = Task.objects.create(
            title="Do thing",
            project=self.project,
            assigned_to=self.assignee,
            created_by=self.manager,
        )

    def _status_url(self):
        return reverse("tasks:status", args=[self.project.pk, self.task.pk])

    def test_status_change_requires_login(self):
        response = self.client.post(self._status_url(), {"status": "DONE"})
        self.assertEqual(response.status_code, 302)

    def test_assignee_can_change_status(self):
        self.client.force_login(self.assignee)
        response = self.client.post(self._status_url(), {"status": "DONE"})
        self.assertRedirects(
            response,
            reverse("tasks:detail", args=[self.project.pk, self.task.pk]),
        )
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, TaskStatus.DONE)

    def test_non_assignee_member_cannot_change_status(self):
        self.client.force_login(self.other)
        response = self.client.post(self._status_url(), {"status": "DONE"})
        self.assertEqual(response.status_code, 403)
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, TaskStatus.TODO)

    def test_invalid_status_rejected(self):
        self.client.force_login(self.assignee)
        response = self.client.post(self._status_url(), {"status": "NOPE"})
        self.assertEqual(response.status_code, 200)
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, TaskStatus.TODO)
