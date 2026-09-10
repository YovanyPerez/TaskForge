from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views.generic import CreateView, DeleteView

from tasks.models import Task
from users.permissions import scope_to_member

from .forms import CommentForm
from .models import Comment


class CommentCreateView(LoginRequiredMixin, CreateView):
    model = Comment
    form_class = CommentForm

    def form_valid(self, form):
        task_qs = scope_to_member(
            Task.objects.all(), self.request.user, project__members=self.request.user
        )
        form.instance.task = get_object_or_404(task_qs, pk=self.kwargs["task_pk"])
        form.instance.user = self.request.user
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, _("Comment cannot be empty."))
        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse(
            "tasks:detail",
            kwargs={
                "project_pk": self.kwargs["project_pk"],
                "pk": self.kwargs["task_pk"],
            },
        )


class CommentDeleteView(LoginRequiredMixin, DeleteView):
    model = Comment
    template_name = "comments/comment_confirm_delete.html"

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if user.is_admin or user.is_manager:
            return qs
        return qs.filter(user=user)

    def get_success_url(self):
        task = self.object.task
        return reverse(
            "tasks:detail",
            kwargs={"project_pk": task.project_id, "pk": task.pk},
        )
