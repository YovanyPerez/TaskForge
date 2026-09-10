from django.urls import include, path
from rest_framework.authtoken import views as auth_views
from rest_framework.routers import DefaultRouter

from comments.viewsets import CommentViewSet
from projects.viewsets import ProjectViewSet
from tasks.viewsets import TaskViewSet
from users.viewsets import UserViewSet

router = DefaultRouter()
router.register("users", UserViewSet, basename="user")
router.register("projects", ProjectViewSet, basename="project")
router.register("tasks", TaskViewSet, basename="task")
router.register("comments", CommentViewSet, basename="comment")

app_name = "api"

urlpatterns = [
    path("token-auth/", auth_views.obtain_auth_token),
    path("", include(router.urls)),
]
