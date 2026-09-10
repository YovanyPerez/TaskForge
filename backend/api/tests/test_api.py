from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from comments.models import Comment
from projects.models import Project
from tasks.models import Task
from users.models import Role

User = get_user_model()


class UsersApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="alice", password="pass12345")

    def test_users_requires_auth(self):
        response = self.client.get("/api/users/")
        self.assertIn(response.status_code, (401, 403))

    def test_users_read_only(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            "/api/users/", {"username": "bob", "password": "pass12345"}
        )
        self.assertEqual(response.status_code, 405)


class ProjectsApiTests(APITestCase):
    def setUp(self):
        self.manager = User.objects.create_user(
            username="mg", role=Role.MANAGER, password="pass12345"
        )
        self.member = User.objects.create_user(
            username="mb", role=Role.MEMBER, password="pass12345"
        )
        self.project = Project.objects.create(name="Alpha", created_by=self.manager)
        self.project.members.add(self.member)

    def test_projects_requires_auth(self):
        response = self.client.get("/api/projects/")
        self.assertIn(response.status_code, (401, 403))

    def test_member_sees_only_their_projects(self):
        Project.objects.create(name="Secret", created_by=self.manager)
        self.client.force_authenticate(user=self.member)
        response = self.client.get("/api/projects/")
        self.assertEqual(response.status_code, 200)
        names = [p["name"] for p in response.data["results"]]
        self.assertIn("Alpha", names)
        self.assertNotIn("Secret", names)

    def test_manager_sees_all_projects(self):
        Project.objects.create(name="Beta", created_by=self.manager)
        self.client.force_authenticate(user=self.manager)
        response = self.client.get("/api/projects/")
        names = [p["name"] for p in response.data["results"]]
        self.assertIn("Alpha", names)
        self.assertIn("Beta", names)

    def test_member_cannot_create_project(self):
        self.client.force_authenticate(user=self.member)
        response = self.client.post(
            "/api/projects/", {"name": "X", "status": "PLANNING"}
        )
        self.assertEqual(response.status_code, 403)

    def test_manager_can_create_project(self):
        self.client.force_authenticate(user=self.manager)
        response = self.client.post(
            "/api/projects/", {"name": "Beta", "status": "PLANNING"}
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["created_by"], self.manager.id)

    def test_project_end_date_before_start_date_rejected(self):
        self.client.force_authenticate(user=self.manager)
        response = self.client.post(
            "/api/projects/",
            {
                "name": "Bad dates",
                "status": "PLANNING",
                "start_date": "2026-09-09",
                "end_date": "2026-09-03",
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("end_date", response.data)

    def test_member_cannot_update_project(self):
        self.client.force_authenticate(user=self.member)
        response = self.client.patch(
            f"/api/projects/{self.project.id}/", {"name": "Hacked"}
        )
        self.assertEqual(response.status_code, 403)

    def test_member_cannot_delete_project(self):
        self.client.force_authenticate(user=self.member)
        response = self.client.delete(f"/api/projects/{self.project.id}/")
        self.assertEqual(response.status_code, 403)


class TasksApiTests(APITestCase):
    def setUp(self):
        self.manager = User.objects.create_user(
            username="mg", role=Role.MANAGER, password="pass12345"
        )
        self.member = User.objects.create_user(
            username="mb", role=Role.MEMBER, password="pass12345"
        )
        self.project = Project.objects.create(name="Alpha", created_by=self.manager)
        self.project.members.add(self.member)

    def test_task_crud_as_manager(self):
        self.client.force_authenticate(user=self.manager)
        response = self.client.post(
            "/api/tasks/",
            {
                "title": "T1",
                "project": self.project.id,
                "priority": "HIGH",
                "status": "TODO",
            },
        )
        self.assertEqual(response.status_code, 201)
        task_id = response.data["id"]
        self.assertEqual(response.data["created_by"], self.manager.id)

        response = self.client.get(f"/api/tasks/{task_id}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["title"], "T1")

        response = self.client.patch(f"/api/tasks/{task_id}/", {"status": "DONE"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], "DONE")

        response = self.client.delete(f"/api/tasks/{task_id}/")
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Task.objects.filter(pk=task_id).exists())

    def test_member_cannot_create_task(self):
        self.client.force_authenticate(user=self.member)
        response = self.client.post(
            "/api/tasks/",
            {
                "title": "T1",
                "project": self.project.id,
                "priority": "HIGH",
                "status": "TODO",
            },
        )
        self.assertEqual(response.status_code, 403)

    def test_member_cannot_update_task(self):
        task = Task.objects.create(
            title="T1", project=self.project, created_by=self.manager
        )
        self.client.force_authenticate(user=self.member)
        response = self.client.patch(f"/api/tasks/{task.id}/", {"status": "DONE"})
        self.assertEqual(response.status_code, 403)

    def test_member_cannot_delete_task(self):
        task = Task.objects.create(
            title="T1", project=self.project, created_by=self.manager
        )
        self.client.force_authenticate(user=self.member)
        response = self.client.delete(f"/api/tasks/{task.id}/")
        self.assertEqual(response.status_code, 403)


class CommentsApiTests(APITestCase):
    def setUp(self):
        self.manager = User.objects.create_user(
            username="mg", role=Role.MANAGER, password="pass12345"
        )
        self.member = User.objects.create_user(
            username="mb", role=Role.MEMBER, password="pass12345"
        )
        self.other = User.objects.create_user(
            username="ot", role=Role.MEMBER, password="pass12345"
        )
        self.project = Project.objects.create(name="Alpha", created_by=self.manager)
        self.project.members.add(self.member, self.other)
        self.task = Task.objects.create(
            title="T1", project=self.project, created_by=self.manager
        )

    def test_comment_create_sets_user(self):
        self.client.force_authenticate(user=self.member)
        response = self.client.post(
            "/api/comments/", {"task": self.task.id, "content": "Looks good"}
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["user"], self.member.id)

    def test_non_member_cannot_comment(self):
        outsider = User.objects.create_user(
            username="out", role=Role.MEMBER, password="pass12345"
        )
        self.client.force_authenticate(user=outsider)
        response = self.client.post(
            "/api/comments/", {"task": self.task.id, "content": "Hi"}
        )
        self.assertEqual(response.status_code, 403)

    def test_member_cannot_delete_others_comment(self):
        comment = Comment.objects.create(task=self.task, user=self.member, content="Hi")
        self.client.force_authenticate(user=self.other)
        response = self.client.delete(f"/api/comments/{comment.id}/")
        self.assertEqual(response.status_code, 403)

    def test_owner_can_delete_own_comment(self):
        comment = Comment.objects.create(task=self.task, user=self.member, content="Hi")
        self.client.force_authenticate(user=self.member)
        response = self.client.delete(f"/api/comments/{comment.id}/")
        self.assertEqual(response.status_code, 204)


class TokenAuthTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="alice", password="pass12345")

    def test_obtain_token(self):
        response = self.client.post(
            "/api/token-auth/", {"username": "alice", "password": "pass12345"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("token", response.data)

    def test_token_authenticates(self):
        token = self.user.auth_token
        response = self.client.get(
            "/api/projects/", HTTP_AUTHORIZATION=f"Token {token.key}"
        )
        self.assertEqual(response.status_code, 200)

    def test_token_can_create_project(self):
        manager = User.objects.create_user(
            username="mg", role=Role.MANAGER, password="pass12345"
        )
        token = manager.auth_token
        response = self.client.post(
            "/api/projects/",
            {"name": "Beta", "status": "PLANNING"},
            HTTP_AUTHORIZATION=f"Token {token.key}",
        )
        self.assertEqual(response.status_code, 201)
