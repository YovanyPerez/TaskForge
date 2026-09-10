import datetime

from django.db.models import Count, Q
from django.utils import timezone
from django.views.generic import TemplateView

from comments.models import Comment
from projects.models import Project
from tasks.models import Priority, Task, TaskStatus
from users.models import User
from users.permissions import scope_to_member


class DashboardView(TemplateView):
    template_name = "dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        if user.is_authenticated:
            projects = scope_to_member(Project.objects.all(), user, members=user)
            tasks = scope_to_member(Task.objects.all(), user, project__members=user)
            context["total_projects"] = projects.count()
            context["total_tasks"] = tasks.count()
            context["my_tasks"] = tasks.filter(assigned_to=user).count()
            context["completed_tasks"] = tasks.filter(status=TaskStatus.DONE).count()
            context["overdue_tasks"] = (
                tasks.filter(due_date__lt=timezone.now().date())
                .exclude(status=TaskStatus.DONE)
                .count()
            )
            context["total_comments"] = scope_to_member(
                Comment.objects.all(), user, task__project__members=user
            ).count()
            context["recent_projects"] = (
                projects.annotate(
                    total_tasks=Count("tasks", distinct=True),
                    done_tasks=Count(
                        "tasks",
                        filter=Q(tasks__status=TaskStatus.DONE),
                        distinct=True,
                    ),
                ).order_by("-created_at")[:5]
            )
            context["open_tasks"] = (
                tasks.filter(assigned_to=user)
                .exclude(status=TaskStatus.DONE)
                .order_by("-created_at")[:5]
            )
        return context


class ReportsView(TemplateView):
    template_name = "reports.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        if not user.is_authenticated:
            return context
        today = timezone.now().date()
        cutoff = timezone.now() - datetime.timedelta(days=30)
        context["project_health"] = (
            scope_to_member(Project.objects.all(), user, members=user)
            .annotate(
                total_tasks=Count("tasks", distinct=True),
                done_tasks=Count(
                    "tasks",
                    filter=Q(tasks__status=TaskStatus.DONE),
                    distinct=True,
                ),
                open_tasks=Count(
                    "tasks",
                    filter=~Q(tasks__status=TaskStatus.DONE),
                    distinct=True,
                ),
                overdue_tasks=Count(
                    "tasks",
                    filter=Q(tasks__due_date__lt=today)
                    & ~Q(tasks__status=TaskStatus.DONE),
                    distinct=True,
                ),
                unassigned_tasks=Count(
                    "tasks",
                    filter=Q(tasks__assigned_to__isnull=True)
                    & ~Q(tasks__status=TaskStatus.DONE),
                    distinct=True,
                ),
                member_count=Count("members", distinct=True),
            )
            .order_by("name")
        )
        tasks = scope_to_member(Task.objects.all(), user, project__members=user)
        status_rows = {
            row["status"]: row["n"] for row in tasks.values("status").annotate(n=Count("id"))
        }
        priority_rows = {
            row["priority"]: row["n"]
            for row in tasks.values("priority").annotate(n=Count("id"))
        }
        total_visible = tasks.count()
        context["tasks_by_status"] = [
            {
                "key": value.lower(),
                "label": label,
                "count": status_rows.get(value, 0),
                "pct": round(status_rows.get(value, 0) / total_visible * 100)
                if total_visible
                else 0,
            }
            for value, label in TaskStatus.choices
        ]
        context["tasks_by_priority"] = [
            {
                "key": value.lower(),
                "label": label,
                "count": priority_rows.get(value, 0),
                "pct": round(priority_rows.get(value, 0) / total_visible * 100)
                if total_visible
                else 0,
            }
            for value, label in Priority.choices
        ]
        context["overdue_list"] = (
            tasks.filter(due_date__lt=today)
            .exclude(status=TaskStatus.DONE)
            .select_related("project", "assigned_to")
            .order_by("due_date")[:20]
        )
        context["at_risk_list"] = (
            tasks.filter(
                due_date__gte=today,
                due_date__lte=today + datetime.timedelta(days=7),
            )
            .exclude(status=TaskStatus.DONE)
            .select_related("project", "assigned_to")
            .order_by("due_date")[:20]
        )
        members_qs = User.objects.all()
        if not (user.is_admin or user.is_manager):
            members_qs = members_qs.filter(projects__in=user.projects.all()).distinct()
        member_rows = list(
            members_qs.annotate(
                assigned_open=Count(
                    "assigned_tasks",
                    filter=~Q(assigned_tasks__status=TaskStatus.DONE),
                    distinct=True,
                ),
                assigned_done=Count(
                    "assigned_tasks",
                    filter=Q(assigned_tasks__status=TaskStatus.DONE),
                    distinct=True,
                ),
                assigned_overdue=Count(
                    "assigned_tasks",
                    filter=Q(assigned_tasks__due_date__lt=today)
                    & ~Q(assigned_tasks__status=TaskStatus.DONE),
                    distinct=True,
                ),
                comment_count=Count("comments", distinct=True),
                recent_done=Count(
                    "assigned_tasks",
                    filter=Q(
                        assigned_tasks__status=TaskStatus.DONE,
                        assigned_tasks__updated_at__gte=cutoff,
                    ),
                    distinct=True,
                ),
                recent_comments=Count(
                    "comments",
                    filter=Q(comments__created_at__gte=cutoff),
                    distinct=True,
                ),
            ).order_by("username")
        )
        context["workload"] = member_rows
        context["activity"] = [
            member
            for member in member_rows
            if member.recent_done or member.recent_comments
        ]
        return context
