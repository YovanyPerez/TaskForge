from django.urls import path

from . import views

app_name = "projects"

urlpatterns = [
    path("", views.ProjectListView.as_view(), name="list"),
    path("new/", views.ProjectCreateView.as_view(), name="create"),
    path("<int:pk>/", views.ProjectDetailView.as_view(), name="detail"),
    path("<int:pk>/edit/", views.ProjectUpdateView.as_view(), name="update"),
    path("<int:pk>/delete/", views.ProjectDeleteView.as_view(), name="delete"),
    path("<int:pk>/members/add/", views.ProjectMemberAddView.as_view(), name="members-add"),
    path(
        "<int:pk>/members/<int:user_pk>/remove/",
        views.ProjectMemberRemoveView.as_view(),
        name="members-remove",
    ),
]
