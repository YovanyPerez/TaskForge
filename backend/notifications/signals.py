from django.contrib.auth import get_user_model
from django.db.models.signals import m2m_changed, post_save, pre_save
from django.dispatch import receiver

from projects.models import Project, ProjectStatus
from tasks.models import Task, TaskStatus

from .middleware import get_current_user
from .models import Notification, NotificationVerb


def _notify(recipients, verb, actor, project=None, task=None):
    if actor is not None and not getattr(actor, "is_active", True):
        actor = None
    seen = set()
    objects = []
    for recipient in recipients:
        if recipient is None or not recipient.is_active:
            continue
        if actor is not None and recipient.pk == actor.pk:
            continue
        if recipient.pk in seen:
            continue
        seen.add(recipient.pk)
        objects.append(
            Notification(
                recipient=recipient,
                actor=actor,
                verb=verb,
                project=project,
                task=task,
            )
        )
    if objects:
        Notification.objects.bulk_create(objects)


@receiver(pre_save, sender=Task)
def task_pre_save(sender, instance, **kwargs):
    if instance.pk:
        previous = (
            Task.objects.filter(pk=instance.pk)
            .values("status", "assigned_to_id")
            .first()
        )
        instance._previous_status = previous["status"] if previous else None
        instance._previous_assigned_to_id = (
            previous["assigned_to_id"] if previous else None
        )
    else:
        instance._previous_status = None
        instance._previous_assigned_to_id = None


@receiver(post_save, sender=Task)
def task_post_save(sender, instance, created, **kwargs):
    actor = get_current_user()
    previous_assigned = getattr(instance, "_previous_assigned_to_id", None)
    if instance.assigned_to_id and instance.assigned_to_id != previous_assigned:
        _notify(
            [instance.assigned_to],
            NotificationVerb.TASK_ASSIGNED,
            actor,
            project=instance.project,
            task=instance,
        )
    previous_status = getattr(instance, "_previous_status", None)
    if instance.status == TaskStatus.DONE and previous_status != TaskStatus.DONE:
        recipients = []
        if instance.created_by_id:
            recipients.append(instance.created_by)
        recipients.extend(instance.project.members.all())
        _notify(
            recipients,
            NotificationVerb.TASK_COMPLETED,
            actor,
            project=instance.project,
            task=instance,
        )


@receiver(pre_save, sender=Project)
def project_pre_save(sender, instance, **kwargs):
    if instance.pk:
        previous = Project.objects.filter(pk=instance.pk).values("status").first()
        instance._previous_status = previous["status"] if previous else None
    else:
        instance._previous_status = None


@receiver(post_save, sender=Project)
def project_post_save(sender, instance, created, **kwargs):
    previous_status = getattr(instance, "_previous_status", None)
    if (
        instance.status == ProjectStatus.COMPLETED
        and previous_status is not None
        and previous_status != ProjectStatus.COMPLETED
    ):
        _notify(
            instance.members.all(),
            NotificationVerb.PROJECT_COMPLETED,
            get_current_user(),
            project=instance,
        )


@receiver(m2m_changed, sender=Project.members.through)
def project_members_changed(sender, instance, action, pk_set, **kwargs):
    if action == "post_add" and pk_set:
        users = get_user_model().objects.filter(pk__in=pk_set)
        _notify(
            users,
            NotificationVerb.PROJECT_MEMBER_ADDED,
            get_current_user(),
            project=instance,
        )
