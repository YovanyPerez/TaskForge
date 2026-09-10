from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils.translation import gettext as _
from django.views import View
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from users.mixins import ManagerOrAdminRequiredMixin
from users.models import User
from users.permissions import scope_to_member

from .forms import ProjectForm, ProjectMemberForm
from .models import Project


class ProjectListView(LoginRequiredMixin, ListView):
    model = Project
    template_name = "projects/project_list.html"
    context_object_name = "projects"

    def get_queryset(self):
        return scope_to_member(
            Project.objects.all(), self.request.user, members=self.request.user
        )


class ProjectDetailView(LoginRequiredMixin, DetailView):
    model = Project
    template_name = "projects/project_detail.html"
    context_object_name = "project"

    def get_queryset(self):
        return scope_to_member(
            Project.objects.all(), self.request.user, members=self.request.user
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["member_form"] = ProjectMemberForm(project=self.object)
        return context


class ProjectMemberAddView(ManagerOrAdminRequiredMixin, View):
    def post(self, request, pk):
        project = get_object_or_404(Project, pk=pk)
        form = ProjectMemberForm(request.POST, project=project)
        if form.is_valid():
            user = form.cleaned_data["user"]
            project.members.add(user)
            messages.success(
                request,
                _("“%(user)s” added to “%(project)s”.")
                % {"user": user, "project": project},
            )
        else:
            messages.error(request, _("Select a valid user to add."))
        return redirect("projects:detail", pk=project.pk)


class ProjectMemberRemoveView(ManagerOrAdminRequiredMixin, View):
    def post(self, request, pk, user_pk):
        project = get_object_or_404(Project, pk=pk)
        member = get_object_or_404(User, pk=user_pk)
        project.members.remove(member)
        messages.success(
            request,
            _("“%(user)s” removed from “%(project)s”.")
            % {"user": member, "project": project},
        )
        return redirect("projects:detail", pk=project.pk)


class ProjectCreateView(ManagerOrAdminRequiredMixin, CreateView):
    model = Project
    form_class = ProjectForm
    template_name = "projects/project_form.html"
    success_url = reverse_lazy("projects:list")

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        response = super().form_valid(form)
        self.object.members.add(self.request.user)
        return response


class ProjectUpdateView(ManagerOrAdminRequiredMixin, UpdateView):
    model = Project
    form_class = ProjectForm
    template_name = "projects/project_form.html"
    success_url = reverse_lazy("projects:list")


class ProjectDeleteView(ManagerOrAdminRequiredMixin, DeleteView):
    model = Project
    template_name = "projects/project_confirm_delete.html"
    success_url = reverse_lazy("projects:list")
