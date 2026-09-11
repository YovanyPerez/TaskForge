from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from notifications.models import Notification, NotificationVerb
from projects.models import Project
from tasks.models import Task
from users.models import Role

User = get_user_model()


class NotificationViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="alice", role=Role.MEMBER, password="pass12345"
        )
        self.other = User.objects.create_user(
            username="bob", role=Role.MEMBER, password="pass12345"
        )
        self.notification = Notification.objects.create(
            recipient=self.user, verb=NotificationVerb.TASK_COMPLETED
        )

    def test_feed_requires_login(self):
        response = self.client.get(reverse("notifications:feed"))
        self.assertEqual(response.status_code, 302)

    def test_feed_returns_count_and_html(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("notifications:feed"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["count"], 1)

    def test_feed_excludes_read_notifications(self):
        Notification.objects.create(
            recipient=self.user,
            verb=NotificationVerb.TASK_COMPLETED,
            is_read=True,
        )
        self.client.force_login(self.user)
        response = self.client.get(reverse("notifications:feed"))
        data = response.json()
        self.assertEqual(data["count"], 1)
        self.assertEqual(data["html"].count("data-notif-read-url"), 1)

    def test_mark_all_button_hidden_when_no_unread(self):
        Notification.objects.all().delete()
        self.client.force_login(self.user)
        response = self.client.get(reverse("home"))
        self.assertContains(
            response,
            'id="tf-notif-mark-all" method="post" '
            'action="/notifications/read-all/" class="m-0 d-none"',
        )

    def test_mark_read(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("notifications:read", args=[self.notification.pk])
        )
        self.assertEqual(response.status_code, 200)
        self.notification.refresh_from_db()
        self.assertTrue(self.notification.is_read)

    def test_cannot_mark_read_foreign_notification(self):
        self.client.force_login(self.other)
        response = self.client.post(
            reverse("notifications:read", args=[self.notification.pk])
        )
        self.assertEqual(response.status_code, 404)

    def test_mark_all_read(self):
        Notification.objects.create(
            recipient=self.user, verb=NotificationVerb.TASK_COMPLETED
        )
        self.client.force_login(self.user)
        response = self.client.post(reverse("notifications:read-all"), {"next": "/"})
        self.assertEqual(response.status_code, 302)
        self.assertFalse(
            Notification.objects.filter(recipient=self.user, is_read=False).exists()
        )

    def test_badge_and_feed_url_rendered(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("home"))
        self.assertContains(response, 'id="tf-notif-badge"')
        self.assertContains(
            response, 'data-feed-url="' + reverse("notifications:feed") + '"'
        )

    def test_assignment_via_web_records_actor(self):
        manager = User.objects.create_user(
            username="mm", role=Role.MANAGER, password="pass12345"
        )
        member = User.objects.create_user(
            username="aa", role=Role.MEMBER, password="pass12345"
        )
        project = Project.objects.create(name="P", created_by=manager)
        project.members.add(manager, member)
        task = Task.objects.create(title="T", project=project, created_by=manager)
        Notification.objects.all().delete()
        self.client.force_login(manager)
        self.client.post(
            reverse("tasks:update", args=[project.pk, task.pk]),
            {
                "title": "T",
                "priority": "MEDIUM",
                "status": "TODO",
                "assigned_to": member.pk,
            },
        )
        notification = Notification.objects.filter(
            recipient=member, verb=NotificationVerb.TASK_ASSIGNED
        ).first()
        self.assertIsNotNone(notification)
        self.assertEqual(notification.actor, manager)
