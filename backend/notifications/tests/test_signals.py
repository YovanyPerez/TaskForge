from django.contrib.auth import get_user_model
from django.test import TestCase

from notifications.middleware import current_user
from notifications.models import Notification, NotificationVerb
from projects.models import Project
from tasks.models import Task, TaskStatus
from users.models import Role

User = get_user_model()


class NotificationSignalTests(TestCase):
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
        self.project.members.add(self.manager, self.member)
        Notification.objects.all().delete()

    def test_task_creation_with_assignee_notifies(self):
        Task.objects.create(
            title="T1",
            project=self.project,
            assigned_to=self.member,
            created_by=self.manager,
        )
        self.assertTrue(
            Notification.objects.filter(
                recipient=self.member, verb=NotificationVerb.TASK_ASSIGNED
            ).exists()
        )

    def test_reassignment_notifies_new_assignee_only(self):
        task = Task.objects.create(
            title="T1",
            project=self.project,
            assigned_to=self.member,
            created_by=self.manager,
        )
        Notification.objects.all().delete()
        task.assigned_to = self.other
        task.save()
        self.assertTrue(
            Notification.objects.filter(
                recipient=self.other, verb=NotificationVerb.TASK_ASSIGNED
            ).exists()
        )
        self.assertFalse(
            Notification.objects.filter(
                recipient=self.member, verb=NotificationVerb.TASK_ASSIGNED
            ).exists()
        )

    def test_completing_task_notifies_creator_and_members(self):
        task = Task.objects.create(
            title="T1", project=self.project, created_by=self.manager
        )
        Notification.objects.all().delete()
        task.status = TaskStatus.DONE
        task.save()
        recipients = set(
            Notification.objects.filter(
                verb=NotificationVerb.TASK_COMPLETED
            ).values_list("recipient_id", flat=True)
        )
        self.assertIn(self.manager.pk, recipients)
        self.assertIn(self.member.pk, recipients)

    def test_actor_excluded_from_completion(self):
        task = Task.objects.create(
            title="T1", project=self.project, created_by=self.manager
        )
        Notification.objects.all().delete()
        with current_user(self.member):
            task.status = TaskStatus.DONE
            task.save()
        recipients = set(
            Notification.objects.filter(
                verb=NotificationVerb.TASK_COMPLETED
            ).values_list("recipient_id", flat=True)
        )
        self.assertNotIn(self.member.pk, recipients)
        self.assertIn(self.manager.pk, recipients)

    def test_adding_member_notifies_newcomer(self):
        Notification.objects.all().delete()
        newcomer = User.objects.create_user(
            username="nc", role=Role.MEMBER, password="pass12345"
        )
        self.project.members.add(newcomer)
        self.assertTrue(
            Notification.objects.filter(
                recipient=newcomer, verb=NotificationVerb.PROJECT_MEMBER_ADDED
            ).exists()
        )

    def test_completing_project_notifies_members(self):
        Notification.objects.all().delete()
        self.project.status = "COMPLETED"
        self.project.save()
        recipients = set(
            Notification.objects.filter(
                verb=NotificationVerb.PROJECT_COMPLETED
            ).values_list("recipient_id", flat=True)
        )
        self.assertIn(self.manager.pk, recipients)
        self.assertIn(self.member.pk, recipients)

    def test_self_assignment_does_not_notify_actor(self):
        with current_user(self.manager):
            Task.objects.create(
                title="T1",
                project=self.project,
                assigned_to=self.manager,
                created_by=self.manager,
            )
        self.assertFalse(
            Notification.objects.filter(
                recipient=self.manager, verb=NotificationVerb.TASK_ASSIGNED
            ).exists()
        )
