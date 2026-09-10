from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from projects.models import Project
from tasks.models import Task
from users.models import Role

User = get_user_model()


class AllTasksBoardTests(TestCase):
    def setUp(self):
        self.manager = User.objects.create_user(
            username="mg", role=Role.MANAGER, password="pass12345"
        )
        self.member = User.objects.create_user(
            username="mb", role=Role.MEMBER, password="pass12345"
        )
        self.visible_project = Project.objects.create(
            name="Alpha", created_by=self.manager
        )
        self.visible_project.members.add(self.member)
        self.hidden_project = Project.objects.create(
            name="Secret", created_by=self.manager
        )
        self.visible_task = Task.objects.create(
            title="Visible task",
            project=self.visible_project,
            created_by=self.manager,
        )
        self.hidden_task = Task.objects.create(
            title="Hidden task",
            project=self.hidden_project,
            created_by=self.manager,
        )

    def test_board_requires_login(self):
        response = self.client.get(reverse("tasks-board"))
        self.assertEqual(response.status_code, 302)

    def test_member_sees_only_visible_tasks(self):
        self.client.force_login(self.member)
        response = self.client.get(reverse("tasks-board"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Visible task")
        self.assertNotContains(response, "Hidden task")

    def test_manager_sees_all_tasks(self):
        self.client.force_login(self.manager)
        response = self.client.get(reverse("tasks-board"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Visible task")
        self.assertContains(response, "Hidden task")
