from django.test import TestCase

from comments.models import Comment
from projects.models import Project
from tasks.models import Task
from users.models import User


class CommentModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="owner", password="pass12345")
        self.project = Project.objects.create(name="Alpha", created_by=self.user)
        self.task = Task.objects.create(
            title="First task", project=self.project, created_by=self.user
        )

    def test_comment_str(self):
        comment = Comment.objects.create(
            task=self.task, user=self.user, content="Looks good"
        )
        self.assertIn(self.user.username, str(comment))

    def test_comment_belongs_to_task(self):
        comment = Comment.objects.create(
            task=self.task, user=self.user, content="Looks good"
        )
        self.assertIn(comment, self.task.comments.all())

    def test_comment_cascade_on_task_delete(self):
        comment = Comment.objects.create(task=self.task, user=self.user, content="Hi")
        self.task.delete()
        self.assertFalse(Comment.objects.filter(pk=comment.pk).exists())
