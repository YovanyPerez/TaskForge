from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from comments.models import Comment
from projects.models import Project
from tasks.models import Task
from users.models import Role

User = get_user_model()


class CommentTests(TestCase):
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
        self.project.members.add(self.manager, self.member, self.other)
        self.task = Task.objects.create(
            title="Do thing", project=self.project, created_by=self.manager
        )

    def _add_url(self):
        return reverse("comments:add", args=[self.project.pk, self.task.pk])

    def _detail_url(self):
        return reverse("tasks:detail", args=[self.project.pk, self.task.pk])

    def test_add_comment(self):
        self.client.force_login(self.member)
        response = self.client.post(self._add_url(), {"content": "Looks good"})
        self.assertRedirects(response, self._detail_url())
        comment = Comment.objects.get(content="Looks good")
        self.assertEqual(comment.user, self.member)
        self.assertEqual(comment.task, self.task)

    def test_add_comment_requires_login(self):
        response = self.client.post(self._add_url(), {"content": "Hi"})
        self.assertEqual(response.status_code, 302)

    def test_empty_comment_rejected(self):
        self.client.force_login(self.member)
        response = self.client.post(self._add_url(), {"content": ""})
        self.assertRedirects(response, self._detail_url())
        self.assertEqual(Comment.objects.count(), 0)

    def test_comment_shown_on_task_detail(self):
        Comment.objects.create(task=self.task, user=self.member, content="Looks good")
        self.client.force_login(self.member)
        response = self.client.get(self._detail_url())
        self.assertContains(response, "Looks good")

    def test_delete_own_comment(self):
        comment = Comment.objects.create(task=self.task, user=self.member, content="Hi")
        self.client.force_login(self.member)
        response = self.client.post(
            reverse("comments:delete", args=[self.project.pk, self.task.pk, comment.pk])
        )
        self.assertRedirects(response, self._detail_url())
        self.assertFalse(Comment.objects.filter(pk=comment.pk).exists())

    def test_delete_other_comment_forbidden(self):
        comment = Comment.objects.create(task=self.task, user=self.member, content="Hi")
        self.client.force_login(self.other)
        response = self.client.post(
            reverse("comments:delete", args=[self.project.pk, self.task.pk, comment.pk])
        )
        self.assertEqual(response.status_code, 404)
        self.assertTrue(Comment.objects.filter(pk=comment.pk).exists())

    def test_manager_can_delete_any_comment(self):
        comment = Comment.objects.create(task=self.task, user=self.member, content="Hi")
        self.client.force_login(self.manager)
        response = self.client.post(
            reverse("comments:delete", args=[self.project.pk, self.task.pk, comment.pk])
        )
        self.assertRedirects(response, self._detail_url())
        self.assertFalse(Comment.objects.filter(pk=comment.pk).exists())
