from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _

from .models import User


@admin.action(description=_("Approve selected users (activate)"))
def approve_users(modeladmin, request, queryset):
    queryset.update(is_active=True)


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = (
        "username",
        "email",
        "first_name",
        "last_name",
        "role",
        "is_staff",
        "is_active",
    )
    list_filter = ("role", "is_staff", "is_active")
    search_fields = ("username", "email", "first_name", "last_name")
    actions = ("approve_users",)
    fieldsets = UserAdmin.fieldsets + (
        ("TaskForge", {"fields": ("role",)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("TaskForge", {"fields": ("role",)}),
    )
