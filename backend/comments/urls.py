from django.urls import path

from . import views

app_name = "comments"

urlpatterns = [
    path("add/", views.CommentCreateView.as_view(), name="add"),
    path("<int:pk>/delete/", views.CommentDeleteView.as_view(), name="delete"),
]
