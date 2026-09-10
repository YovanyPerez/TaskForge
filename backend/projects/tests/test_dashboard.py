import datetime

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from projects.models import Project
from tasks.models import Task, TaskStatus
from users.models import Role

User = get_user_model()


class DashboardTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="alice", role=Role.MEMBER, password="pass12345"
        )

    def test_anonymous_sees_landing(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Log in")

    def test_dashboard_shows_stats(self):
        self.client.force_login(self.user)
        project = Project.objects.create(name="Alpha", created_by=self.user)
        project.members.add(self.user)
        Task.objects.create(
            title="T1", project=project, assigned_to=self.user, created_by=self.user
        )
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Alpha")
        self.assertContains(response, "T1")

    def test_dashboard_completed_and_overdue_counts(self):
        self.client.force_login(self.user)
        project = Project.objects.create(name="Alpha", created_by=self.user)
        project.members.add(self.user)
        today = timezone.now().date()
        Task.objects.create(
            title="Done task",
            project=project,
            status=TaskStatus.DONE,
            created_by=self.user,
        )
        Task.objects.create(
            title="Overdue task",
            project=project,
            status=TaskStatus.TODO,
            due_date=today - datetime.timedelta(days=1),
            created_by=self.user,
        )
        Task.objects.create(
            title="Upcoming task",
            project=project,
            status=TaskStatus.TODO,
            due_date=today + datetime.timedelta(days=5),
            created_by=self.user,
        )
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["completed_tasks"], 1)
        self.assertEqual(response.context["overdue_tasks"], 1)

    def test_dashboard_project_progress(self):
        self.client.force_login(self.user)
        project = Project.objects.create(name="Alpha", created_by=self.user)
        project.members.add(self.user)
        Task.objects.create(
            title="Done task",
            project=project,
            status=TaskStatus.DONE,
            created_by=self.user,
        )
        Task.objects.create(
            title="Open task",
            project=project,
            status=TaskStatus.TODO,
            created_by=self.user,
        )
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "1/2 tasks done")
