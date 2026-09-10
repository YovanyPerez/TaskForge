import datetime

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from comments.models import Comment
from projects.models import Project
from tasks.models import Task, TaskStatus
from users.models import Role

User = get_user_model()


class ReportsTests(TestCase):
    def setUp(self):
        self.manager = User.objects.create_user(
            username="mg", role=Role.MANAGER, password="pass12345"
        )
        self.alice = User.objects.create_user(
            username="alice", role=Role.MEMBER, password="pass12345"
        )
        self.outsider = User.objects.create_user(
            username="out", role=Role.MEMBER, password="pass12345"
        )
        self.project = Project.objects.create(name="Alpha", created_by=self.manager)
        self.project.members.add(self.alice)
        self.hidden = Project.objects.create(name="Secret", created_by=self.manager)
        today = timezone.now().date()
        self.done_task = Task.objects.create(
            title="Done task",
            project=self.project,
            status=TaskStatus.DONE,
            created_by=self.manager,
        )
        self.overdue_task = Task.objects.create(
            title="Overdue task",
            project=self.project,
            status=TaskStatus.TODO,
            due_date=today - datetime.timedelta(days=2),
            assigned_to=self.alice,
            created_by=self.manager,
        )
        self.secret_task = Task.objects.create(
            title="Secret task",
            project=self.hidden,
            status=TaskStatus.TODO,
            created_by=self.manager,
        )

    def test_anonymous_sees_login_prompt(self):
        response = self.client.get(reverse("reports"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Log in")

    def test_member_does_not_see_other_projects(self):
        self.client.force_login(self.alice)
        response = self.client.get(reverse("reports"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Alpha")
        self.assertNotContains(response, "Secret task")
        self.assertContains(response, "Overdue task")

    def test_manager_sees_everything(self):
        self.client.force_login(self.manager)
        response = self.client.get(reverse("reports"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Alpha")
        self.assertContains(response, "Secret")

    def test_health_counts(self):
        self.client.force_login(self.manager)
        response = self.client.get(reverse("reports"))
        health = {p.name: p for p in response.context["project_health"]}
        self.assertEqual(health["Alpha"].total_tasks, 2)
        self.assertEqual(health["Alpha"].done_tasks, 1)
        self.assertEqual(health["Alpha"].overdue_tasks, 1)

    def test_distribution_counts(self):
        self.client.force_login(self.manager)
        response = self.client.get(reverse("reports"))
        by_status = {row["key"]: row["count"] for row in response.context["tasks_by_status"]}
        self.assertEqual(by_status["done"], 1)
        self.assertEqual(by_status["todo"], 2)

    def test_distribution_bars_are_proportional(self):
        self.client.force_login(self.manager)
        response = self.client.get(reverse("reports"))
        by_status = {row["key"]: row for row in response.context["tasks_by_status"]}
        self.assertEqual(by_status["done"]["pct"], 33)
        self.assertEqual(by_status["todo"]["pct"], 67)
        self.assertEqual(by_status["in_progress"]["pct"], 0)

    def test_activity_last_30_days(self):
        Comment.objects.create(
            task=self.done_task, user=self.alice, content="Nice work"
        )
        old_done = Task.objects.create(
            title="Old done",
            project=self.project,
            status=TaskStatus.DONE,
            created_by=self.manager,
        )
        Task.objects.filter(pk=old_done.pk).update(
            updated_at=timezone.now() - datetime.timedelta(days=60)
        )
        self.client.force_login(self.manager)
        response = self.client.get(reverse("reports"))
        activity = {m.username: m for m in response.context["activity"]}
        self.assertIn("alice", activity)
        self.assertEqual(activity["alice"].recent_comments, 1)
        self.assertEqual(activity["alice"].recent_done, 0)
