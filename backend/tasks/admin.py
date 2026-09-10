from django.contrib import admin

from .models import Task


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "project",
        "assigned_to",
        "priority",
        "status",
        "due_date",
        "created_at",
    )
    list_filter = ("priority", "status", "project")
    search_fields = ("title", "description")
