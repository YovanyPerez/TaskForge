from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Prefetch, Q
from django.urls import reverse_lazy
from django.utils import translation
from django.utils.translation import gettext as _
from django.views.generic import CreateView, DetailView, ListView, UpdateView
from django.views.i18n import set_language as django_set_language

from projects.models import Project
from tasks.models import Task, TaskStatus

from .forms import UserProfileForm, UserRegistrationForm, UserSettingsForm
from .models import User
from .permissions import scope_to_member


class RegisterView(CreateView):
    model = User
    form_class = UserRegistrationForm
    template_name = "users/register.html"
    success_url = reverse_lazy("users:login")

    def form_valid(self, form):
        form.instance.is_active = False
        response = super().form_valid(form)
        messages.success(
            self.request,
            _(
                "Account created. An administrator must approve it before you "
                "can log in."
            ),
        )
        return response


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = UserProfileForm
    template_name = "users/profile.html"
    success_url = reverse_lazy("users:profile")

    def get_object(self, queryset=None):
        return self.request.user


class SettingsView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = UserSettingsForm
    template_name = "users/settings.html"
    success_url = reverse_lazy("users:settings")

    def get_object(self, queryset=None):
        return self.request.user

    def form_valid(self, form):
        response = super().form_valid(form)
        language = form.cleaned_data.get("language") or settings.LANGUAGE_CODE
        translation.activate(language)
        messages.success(self.request, _("Settings saved."))
        return response


def switch_language(request):
    """Save the preference on the profile, then delegate to Django's own view
    (it validates the language and sets the locale cookie)."""
    if request.method == "POST":
        language = request.POST.get("language", "")
        if language not in dict(settings.LANGUAGES):
            language = "en"
            request.POST = request.POST.copy()
            request.POST["language"] = language
        user = getattr(request, "user", None)
        if getattr(user, "is_authenticated", False) and user.language != language:
            user.language = language
            user.save(update_fields=["language", "updated_at"])
    return django_set_language(request)


class TeamListView(LoginRequiredMixin, ListView):
    model = User
    template_name = "users/team_list.html"
    context_object_name = "members"

    def get_queryset(self):
        user = self.request.user
        qs = User.objects.all()
        if not (user.is_admin or user.is_manager):
            qs = qs.filter(projects__in=user.projects.all()).distinct()
        visible_project_ids = scope_to_member(
            Project.objects.all(), user, members=user
        ).values("pk")
        return (
            qs.annotate(
                open_task_count=Count(
                    "assigned_tasks",
                    filter=~Q(assigned_tasks__status=TaskStatus.DONE),
                    distinct=True,
                ),
            )
            .prefetch_related(
                Prefetch(
                    "projects",
                    queryset=Project.objects.filter(
                        pk__in=visible_project_ids
                    ).order_by("name"),
                    to_attr="visible_projects",
                )
            )
            .order_by("username")
        )


class TeamDetailView(LoginRequiredMixin, DetailView):
    model = User
    template_name = "users/team_detail.html"
    context_object_name = "member"

    def get_queryset(self):
        user = self.request.user
        qs = User.objects.all()
        if not (user.is_admin or user.is_manager):
            qs = qs.filter(projects__in=user.projects.all()).distinct()
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        viewer = self.request.user
        member = self.object
        if viewer.is_admin or viewer.is_manager:
            member_projects = member.projects.all()
        else:
            # Forward chained filters (separate JOINs). Filtering on the
            # reverse manager (member.projects.filter(members=viewer)) would
            # AND both conditions onto a single JOIN and always return empty.
            member_projects = Project.objects.filter(members=member).filter(
                members=viewer
            )
        context["member_projects"] = member_projects.order_by("-created_at")
        context["member_project_count"] = member_projects.count()
        context["member_tasks"] = (
            Task.objects.filter(assigned_to=member, project__in=member_projects)
            .exclude(status=TaskStatus.DONE)
            .select_related("project")
            .order_by("-created_at")[:10]
        )
        return context
