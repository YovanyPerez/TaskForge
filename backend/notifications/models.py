from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _


class NotificationVerb(models.TextChoices):
    TASK_ASSIGNED = "TASK_ASSIGNED", _("Task assigned")
    PROJECT_MEMBER_ADDED = "PROJECT_MEMBER_ADDED", _("Added to project")
    TASK_COMPLETED = "TASK_COMPLETED", _("Task completed")
    PROJECT_COMPLETED = "PROJECT_COMPLETED", _("Project completed")


class Notification(models.Model):
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )
    verb = models.CharField(max_length=32, choices=NotificationVerb.choices)
    project = models.ForeignKey(
        "projects.Project",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="notifications",
    )
    task = models.ForeignKey(
        "tasks.Task",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="notifications",
    )
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["recipient", "is_read"])]

    def __str__(self) -> str:
        return f"{self.get_verb_display()} -> {self.recipient}"

    def get_url(self) -> str:
        if self.task_id:
            return reverse(
                "tasks:detail",
                kwargs={"project_pk": self.task.project_id, "pk": self.task_id},
            )
        if self.project_id:
            return reverse("projects:detail", kwargs={"pk": self.project_id})
        return ""
