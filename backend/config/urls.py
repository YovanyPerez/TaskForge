from django.contrib import admin
from django.urls import include, path

from . import views
from tasks import views as task_views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("users.urls")),
    path("projects/", include("projects.urls")),
    path("tasks/", task_views.AllTasksBoardView.as_view(), name="tasks-board"),
    path("projects/<int:project_pk>/tasks/", include("tasks.urls")),
    path(
        "projects/<int:project_pk>/tasks/<int:task_pk>/comments/",
        include("comments.urls"),
    ),
    path("api/", include("api.urls")),
    path("", views.DashboardView.as_view(), name="home"),
    path("reports/", views.ReportsView.as_view(), name="reports"),
]
