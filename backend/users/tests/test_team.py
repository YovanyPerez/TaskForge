from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from projects.models import Project
from tasks.models import Task
from users.models import Role

User = get_user_model()


class TeamTests(TestCase):
    def setUp(self):
        self.manager = User.objects.create_user(
            username="mg", role=Role.MANAGER, password="pass12345"
        )
        self.alice = User.objects.create_user(
            username="alice", role=Role.MEMBER, password="pass12345"
        )
        self.bob = User.objects.create_user(
            username="bob", role=Role.MEMBER, password="pass12345"
        )
        self.outsider = User.objects.create_user(
            username="out", role=Role.MEMBER, password="pass12345"
        )
        self.project = Project.objects.create(name="Alpha", created_by=self.manager)
        self.project.members.add(self.alice, self.bob)
        self.task = Task.objects.create(
            title="Do thing",
            project=self.project,
            assigned_to=self.alice,
            created_by=self.manager,
        )

    def test_team_list_requires_login(self):
        response = self.client.get(reverse("users:team-list"))
        self.assertEqual(response.status_code, 302)

    def test_member_sees_only_teammates(self):
        self.client.force_login(self.alice)
        response = self.client.get(reverse("users:team-list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response, reverse("users:team-detail", args=[self.alice.pk])
        )
        self.assertContains(response, reverse("users:team-detail", args=[self.bob.pk]))
        self.assertNotContains(
            response, reverse("users:team-detail", args=[self.outsider.pk])
        )

    def test_manager_sees_everyone(self):
        self.client.force_login(self.manager)
        response = self.client.get(reverse("users:team-list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response, reverse("users:team-detail", args=[self.alice.pk])
        )
        self.assertContains(response, reverse("users:team-detail", args=[self.bob.pk]))
        self.assertContains(
            response, reverse("users:team-detail", args=[self.outsider.pk])
        )

    def test_member_detail_of_non_teammate_is_404(self):
        self.client.force_login(self.alice)
        response = self.client.get(reverse("users:team-detail", args=[self.outsider.pk]))
        self.assertEqual(response.status_code, 404)

    def test_manager_can_view_any_detail(self):
        self.client.force_login(self.manager)
        response = self.client.get(reverse("users:team-detail", args=[self.outsider.pk]))
        self.assertEqual(response.status_code, 200)

    def test_manager_list_shows_member_projects(self):
        self.client.force_login(self.manager)
        response = self.client.get(reverse("users:team-list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Alpha")
        self.assertContains(
            response, reverse("projects:detail", args=[self.project.pk])
        )

    def test_member_list_hides_projects_not_shared(self):
        hidden = Project.objects.create(name="Hidden", created_by=self.manager)
        hidden.members.add(self.bob)
        self.client.force_login(self.alice)
        response = self.client.get(reverse("users:team-list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Alpha")
        self.assertNotContains(response, "Hidden")

    def test_member_project_count_only_counts_shared(self):
        hidden = Project.objects.create(name="Hidden", created_by=self.manager)
        hidden.members.add(self.bob)
        self.client.force_login(self.alice)
        response = self.client.get(reverse("users:team-list"))
        bob = next(m for m in response.context["members"] if m.username == "bob")
        self.assertEqual(len(bob.visible_projects), 1)

    def test_detail_shows_projects_and_tasks(self):
        self.client.force_login(self.bob)
        response = self.client.get(reverse("users:team-detail", args=[self.alice.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Alpha")
        self.assertContains(response, "Do thing")
