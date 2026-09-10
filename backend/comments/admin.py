from django.contrib import admin

from .models import Comment


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("task", "user", "created_at")
    list_filter = ("created_at",)
    search_fields = ("content", "task__title", "user__username")
