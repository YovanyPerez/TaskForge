from django import forms
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

from .models import Project


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ("name", "description", "start_date", "end_date", "status")
        labels = {
            "name": _("Name"),
            "description": _("Description"),
            "start_date": _("Start date"),
            "end_date": _("End date"),
            "status": _("Status"),
        }
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
            "start_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "end_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "status": forms.Select(attrs={"class": "form-control"}),
        }


class ProjectMemberForm(forms.Form):
    user = forms.ModelChoiceField(
        queryset=get_user_model().objects.none(),
        widget=forms.Select(attrs={"class": "form-control"}),
        label=_("Add member"),
    )

    def __init__(self, *args, project=None, **kwargs):
        super().__init__(*args, **kwargs)
        if project is not None:
            self.fields["user"].queryset = (
                get_user_model()
                .objects.exclude(pk__in=project.members.values_list("pk", flat=True))
                .order_by("username")
            )
