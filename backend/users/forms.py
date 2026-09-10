from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.utils.translation import gettext_lazy as _

from .models import User


def _apply_bootstrap(form: forms.Form) -> None:
    for field in form.fields.values():
        field.widget.attrs["class"] = "form-control"


class UserLoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _apply_bootstrap(self)


class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True, label=_("Email address"))
    first_name = forms.CharField(
        max_length=150, required=False, label=_("First name")
    )
    last_name = forms.CharField(max_length=150, required=False, label=_("Last name"))

    class Meta:
        model = User
        fields = (
            "username",
            "email",
            "first_name",
            "last_name",
            "password1",
            "password2",
        )
        labels = {"username": _("Username")}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _apply_bootstrap(self)


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("first_name", "last_name", "email")
        labels = {
            "first_name": _("First name"),
            "last_name": _("Last name"),
            "email": _("Email address"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _apply_bootstrap(self)


class UserSettingsForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("language",)
        labels = {"language": _("Language")}
        help_texts = {"language": _("Choose the interface language.")}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _apply_bootstrap(self)
        self.fields["language"].empty_label = _("System default")
