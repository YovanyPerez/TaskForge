from django.contrib import admin

from .models import Project


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "status",
        "start_date",
        "end_date",
        "created_by",
        "created_at",
    )
    list_filter = ("status",)
    search_fields = ("name", "description")
    filter_horizontal = ("members",)
