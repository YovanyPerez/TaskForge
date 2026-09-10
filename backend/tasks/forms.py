from django import forms
from django.utils.translation import gettext_lazy as _

from .models import Task


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ("title", "description", "assigned_to", "priority", "status", "due_date")
        labels = {
            "title": _("Title"),
            "description": _("Description"),
            "assigned_to": _("Assigned to"),
            "priority": _("Priority"),
            "status": _("Status"),
            "due_date": _("Due date"),
        }
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
            "assigned_to": forms.Select(attrs={"class": "form-control"}),
            "priority": forms.Select(attrs={"class": "form-control"}),
            "status": forms.Select(attrs={"class": "form-control"}),
            "due_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        project = kwargs.pop("project", None)
        super().__init__(*args, **kwargs)
        if project is not None:
            self.fields["assigned_to"].queryset = project.members.all()


class TaskStatusForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ("status",)
        labels = {"status": _("Status")}
        widgets = {
            "status": forms.Select(attrs={"class": "form-control"}),
        }
