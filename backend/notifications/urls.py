from django.urls import path

from . import views

app_name = "notifications"

urlpatterns = [
    path("feed/", views.feed, name="feed"),
    path("read-all/", views.mark_all_read, name="read-all"),
    path("<int:pk>/read/", views.mark_read, name="read"),
]
