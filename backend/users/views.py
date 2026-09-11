from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils import translation
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.translation import gettext as _
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from projects.models import Project
from tasks.models import Task, TaskStatus

from .forms import UserProfileForm, UserRegistrationForm, UserSettingsForm
from .models import User


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
    """Switch interface language: session always, profile when logged in."""
    if request.method != "POST":
        return redirect("home")
    language = request.POST.get("language", "")
    valid = dict(settings.LANGUAGES)
    if language not in valid:
        language = "en"
    translation.activate(language)
    user = getattr(request, "user", None)
    if getattr(user, "is_authenticated", False):
        user.language = language
        user.save(update_fields=["language", "updated_at"])
    next_url = request.POST.get("next") or reverse_lazy("home")
    if not url_has_allowed_host_and_scheme(next_url, allowed_hosts=None):
        next_url = reverse_lazy("home")
    response = redirect(next_url)
    # LocaleMiddleware reads this cookie (same as Django's set_language view).
    response.set_cookie(
        settings.LANGUAGE_COOKIE_NAME,
        language,
        max_age=settings.LANGUAGE_COOKIE_AGE,
        path=settings.LANGUAGE_COOKIE_PATH,
        samesite=settings.LANGUAGE_COOKIE_SAMESITE,
    )
    return response


class TeamListView(LoginRequiredMixin, ListView):
    model = User
    template_name = "users/team_list.html"
    context_object_name = "members"

    def get_queryset(self):
        user = self.request.user
        qs = User.objects.all()
        if not (user.is_admin or user.is_manager):
            qs = qs.filter(projects__in=user.projects.all()).distinct()
        return qs.annotate(
            project_count=Count("projects", distinct=True),
            open_task_count=Count(
                "assigned_tasks",
                filter=~Q(assigned_tasks__status=TaskStatus.DONE),
                distinct=True,
            ),
        ).order_by("username")


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
