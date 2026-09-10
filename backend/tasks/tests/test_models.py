from django.test import TestCase

from projects.models import Project
from tasks.models import Priority, Task, TaskStatus
from users.models import User


class TaskModelTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="owner", password="pass12345")
        self.project = Project.objects.create(name="Alpha", created_by=self.owner)

    def test_task_defaults(self):
        task = Task.objects.create(
            title="First task", project=self.project, created_by=self.owner
        )
        self.assertEqual(task.priority, Priority.MEDIUM)
        self.assertEqual(task.status, TaskStatus.TODO)

    def test_task_str(self):
        task = Task.objects.create(
            title="First task", project=self.project, created_by=self.owner
        )
        self.assertEqual(str(task), "First task")

    def test_task_belongs_to_project(self):
        task = Task.objects.create(
            title="First task", project=self.project, created_by=self.owner
        )
        self.assertIn(task, self.project.tasks.all())

    def test_task_cascade_on_project_delete(self):
        task = Task.objects.create(
            title="First task", project=self.project, created_by=self.owner
        )
        self.project.delete()
        self.assertFalse(Task.objects.filter(pk=task.pk).exists())
