from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from projects.models import Project
from users.models import Role

User = get_user_model()


class ProjectCrudTests(TestCase):
    def setUp(self):
        self.manager = User.objects.create_user(
            username="mg", role=Role.MANAGER, password="pass12345"
        )
        self.member = User.objects.create_user(
            username="mb", role=Role.MEMBER, password="pass12345"
        )

    def test_list_requires_login(self):
        response = self.client.get(reverse("projects:list"))
        self.assertEqual(response.status_code, 302)

    def test_list(self):
        self.client.force_login(self.member)
        project = Project.objects.create(name="Alpha", created_by=self.manager)
        project.members.add(self.member)
        response = self.client.get(reverse("projects:list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Alpha")

    def test_member_does_not_see_other_projects(self):
        self.client.force_login(self.member)
        Project.objects.create(name="Secret", created_by=self.manager)
        response = self.client.get(reverse("projects:list"))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Secret")

    def test_detail_requires_membership(self):
        self.client.force_login(self.member)
        project = Project.objects.create(name="Secret", created_by=self.manager)
        response = self.client.get(reverse("projects:detail", args=[project.pk]))
        self.assertEqual(response.status_code, 404)

    def test_create_requires_manager(self):
        self.client.force_login(self.member)
        response = self.client.get(reverse("projects:create"))
        self.assertEqual(response.status_code, 403)

    def test_create(self):
        self.client.force_login(self.manager)
        response = self.client.post(
            reverse("projects:create"),
            {
                "name": "Alpha",
                "description": "First project",
                "status": "PLANNING",
                "start_date": "2026-01-01",
                "end_date": "2026-12-31",
            },
        )
        self.assertRedirects(response, reverse("projects:list"))
        project = Project.objects.get(name="Alpha")
        self.assertEqual(project.created_by, self.manager)
        self.assertIn(self.manager, project.members.all())

    def test_create_with_members(self):
        self.client.force_login(self.manager)
        response = self.client.post(
            reverse("projects:create"),
            {
                "name": "Alpha",
                "description": "",
                "status": "PLANNING",
                "start_date": "",
                "end_date": "",
                "members": [self.member.pk],
            },
        )
        self.assertRedirects(response, reverse("projects:list"))
        project = Project.objects.get(name="Alpha")
        self.assertIn(self.manager, project.members.all())
        self.assertIn(self.member, project.members.all())

    def test_create_form_has_members_field(self):
        self.client.force_login(self.manager)
        response = self.client.get(reverse("projects:create"))
        self.assertIn("members", response.context["form"].fields)

    def test_update_form_has_no_members_field(self):
        self.client.force_login(self.manager)
        project = Project.objects.create(name="Alpha", created_by=self.manager)
        response = self.client.get(reverse("projects:update", args=[project.pk]))
        self.assertNotIn("members", response.context["form"].fields)

    def test_update(self):
        self.client.force_login(self.manager)
        project = Project.objects.create(name="Alpha", created_by=self.manager)
        response = self.client.post(
            reverse("projects:update", args=[project.pk]),
            {"name": "Alpha v2", "description": "", "status": "IN_PROGRESS"},
        )
        self.assertRedirects(response, reverse("projects:list"))
        project.refresh_from_db()
        self.assertEqual(project.name, "Alpha v2")
        self.assertEqual(project.status, "IN_PROGRESS")

    def test_delete(self):
        self.client.force_login(self.manager)
        project = Project.objects.create(name="Alpha", created_by=self.manager)
        response = self.client.post(reverse("projects:delete", args=[project.pk]))
        self.assertRedirects(response, reverse("projects:list"))
        self.assertFalse(Project.objects.filter(pk=project.pk).exists())

    def test_delete_requires_manager(self):
        self.client.force_login(self.member)
        project = Project.objects.create(name="Alpha", created_by=self.manager)
        response = self.client.post(reverse("projects:delete", args=[project.pk]))
        self.assertEqual(response.status_code, 403)
        self.assertTrue(Project.objects.filter(pk=project.pk).exists())


class ProjectMemberTests(TestCase):
    def setUp(self):
        self.manager = User.objects.create_user(
            username="mg", role=Role.MANAGER, password="pass12345"
        )
        self.member = User.objects.create_user(
            username="mb", role=Role.MEMBER, password="pass12345"
        )
        self.newcomer = User.objects.create_user(
            username="nc", role=Role.MEMBER, password="pass12345"
        )
        self.project = Project.objects.create(name="Alpha", created_by=self.manager)
        self.project.members.add(self.member)

    def test_manager_can_add_member(self):
        self.client.force_login(self.manager)
        response = self.client.post(
            reverse("projects:members-add", args=[self.project.pk]),
            {"user": self.newcomer.pk},
        )
        self.assertRedirects(
            response, reverse("projects:detail", args=[self.project.pk])
        )
        self.assertIn(self.newcomer, self.project.members.all())

    def test_member_cannot_add_member(self):
        self.client.force_login(self.member)
        response = self.client.post(
            reverse("projects:members-add", args=[self.project.pk]),
            {"user": self.newcomer.pk},
        )
        self.assertEqual(response.status_code, 403)
        self.assertNotIn(self.newcomer, self.project.members.all())

    def test_manager_can_remove_member(self):
        self.client.force_login(self.manager)
        response = self.client.post(
            reverse(
                "projects:members-remove", args=[self.project.pk, self.member.pk]
            )
        )
        self.assertRedirects(
            response, reverse("projects:detail", args=[self.project.pk])
        )
        self.assertNotIn(self.member, self.project.members.all())

    def test_member_cannot_remove_member(self):
        self.client.force_login(self.member)
        response = self.client.post(
            reverse(
                "projects:members-remove", args=[self.project.pk, self.member.pk]
            )
        )
        self.assertEqual(response.status_code, 403)
        self.assertIn(self.member, self.project.members.all())
