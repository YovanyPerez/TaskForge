import re

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


class SpecialCharacterValidator:
    """Require at least one non-alphanumeric character in passwords."""

    def validate(self, password, user=None):
        if password is None or not re.search(r"[^A-Za-z0-9]", password):
            raise ValidationError(
                _(
                    "Your password must contain at least one special character "
                    "(e.g. !@#$%)."
                ),
                code="password_no_special_character",
            )

    def get_help_text(self):
        return _(
            "Your password must contain at least one special character (e.g. !@#$%)."
        )
