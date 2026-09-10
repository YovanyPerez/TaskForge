from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from comments.forms import CommentForm
from projects.models import Project
from users.mixins import ManagerOrAdminRequiredMixin
from users.permissions import scope_to_member

from .forms import TaskForm, TaskStatusForm
from .models import Task


class ProjectTasksMixin:
    def get_project(self):
        qs = scope_to_member(
            Project.objects.all(), self.request.user, members=self.request.user
        )
        return get_object_or_404(qs, pk=self.kwargs["project_pk"])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        return context


class TaskListView(LoginRequiredMixin, ProjectTasksMixin, ListView):
    model = Task
    template_name = "tasks/task_list.html"
    context_object_name = "tasks"

    def get_queryset(self):
        return scope_to_member(
            Task.objects.filter(project=self.get_project()).order_by("-created_at"),
            self.request.user,
            project__members=self.request.user,
        )


class AllTasksBoardView(LoginRequiredMixin, ListView):
    model = Task
    template_name = "tasks/task_board.html"
    context_object_name = "tasks"

    def get_queryset(self):
        return (
            scope_to_member(
                Task.objects.all(),
                self.request.user,
                project__members=self.request.user,
            )
            .select_related("project", "assigned_to")
            .order_by("project__name", "-created_at")
        )


class TaskCreateView(ManagerOrAdminRequiredMixin, ProjectTasksMixin, CreateView):
    model = Task
    form_class = TaskForm
    template_name = "tasks/task_form.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["project"] = self.get_project()
        return kwargs

    def form_valid(self, form):
        form.instance.project = self.get_project()
        form.instance.created_by = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("tasks:list", kwargs={"project_pk": self.kwargs["project_pk"]})


class TaskDetailView(LoginRequiredMixin, DetailView):
    model = Task
    template_name = "tasks/task_detail.html"
    context_object_name = "task"

    def get_queryset(self):
        return scope_to_member(
            Task.objects.all(), self.request.user, project__members=self.request.user
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["comments"] = self.object.comments.all()
        context["comment_form"] = CommentForm()
        context["status_form"] = TaskStatusForm(instance=self.object)
        return context


class TaskUpdateView(ManagerOrAdminRequiredMixin, UpdateView):
    model = Task
    form_class = TaskForm
    template_name = "tasks/task_form.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["project"] = self.object.project
        return kwargs

    def get_success_url(self):
        return reverse("tasks:list", kwargs={"project_pk": self.object.project_id})


class TaskStatusUpdateView(LoginRequiredMixin, UpdateView):
    """Let the assigned user (or an admin/manager) change only a task's status."""

    model = Task
    form_class = TaskStatusForm
    template_name = "tasks/task_status_form.html"

    def get_queryset(self):
        return scope_to_member(
            Task.objects.all(), self.request.user, project__members=self.request.user
        )

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        task = self.get_object()
        user = request.user
        if task.assigned_to_id != user.pk and not (
            user.is_admin or user.is_manager
        ):
            raise PermissionDenied(
                _(
                    "Only the assigned user, a manager, or an admin can change "
                    "this task's status."
                )
            )
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse(
            "tasks:detail",
            kwargs={"project_pk": self.object.project_id, "pk": self.object.pk},
        )


class TaskDeleteView(ManagerOrAdminRequiredMixin, DeleteView):
    model = Task
    template_name = "tasks/task_confirm_delete.html"

    def get_success_url(self):
        return reverse("tasks:list", kwargs={"project_pk": self.object.project_id})
