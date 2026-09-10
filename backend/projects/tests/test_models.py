from django.test import TestCase

from projects.models import Project, ProjectStatus
from users.models import User


class ProjectModelTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="owner", password="pass12345")

    def test_project_default_status(self):
        project = Project.objects.create(name="Alpha", created_by=self.owner)
        self.assertEqual(project.status, ProjectStatus.PLANNING)

    def test_project_str(self):
        project = Project.objects.create(name="Alpha", created_by=self.owner)
        self.assertEqual(str(project), "Alpha")

    def test_project_members(self):
        member = User.objects.create_user(username="member", password="pass12345")
        project = Project.objects.create(name="Alpha", created_by=self.owner)
        project.members.add(member)
        self.assertIn(member, project.members.all())
