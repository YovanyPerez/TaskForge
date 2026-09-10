from django.test import TestCase

from users.models import Role, User


class UserModelTests(TestCase):
    def test_create_user_with_default_role(self):
        user = User.objects.create_user(
            username="alice", password="pass12345", email="alice@example.com"
        )
        self.assertEqual(user.role, Role.MEMBER)

    def test_user_str(self):
        user = User.objects.create_user(username="alice", password="pass12345")
        self.assertEqual(str(user), "alice")

    def test_create_superuser(self):
        user = User.objects.create_superuser(
            username="admin", password="pass12345", email="admin@example.com"
        )
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)
