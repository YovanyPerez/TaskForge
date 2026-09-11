from django.contrib import admin

from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = (
        "recipient",
        "verb",
        "actor",
        "project",
        "task",
        "is_read",
        "created_at",
    )
    list_filter = ("is_read", "verb")
    search_fields = ("recipient__username", "actor__username")
    readonly_fields = ("created_at",)
