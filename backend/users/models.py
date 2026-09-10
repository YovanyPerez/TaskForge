from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class Role(models.TextChoices):
    ADMIN = "ADMIN", _("Admin")
    MANAGER = "MANAGER", _("Manager")
    MEMBER = "MEMBER", _("Member")


class User(AbstractUser):
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.MEMBER)
    language = models.CharField(
        max_length=10, choices=settings.LANGUAGES, default="", blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["username"]

    @property
    def is_admin(self) -> bool:
        return self.role == Role.ADMIN

    @property
    def is_manager(self) -> bool:
        return self.role == Role.MANAGER

    @property
    def is_member(self) -> bool:
        return self.role == Role.MEMBER

    def __str__(self) -> str:
        return self.username
