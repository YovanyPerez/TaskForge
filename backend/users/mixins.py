from django.contrib.auth.mixins import UserPassesTestMixin

from .models import Role


class ManagerOrAdminRequiredMixin(UserPassesTestMixin):
    """Allow only ADMIN and MANAGER roles. Anonymous users are redirected to login."""

    def test_func(self):
        user = self.request.user
        return user.is_authenticated and user.role in (Role.ADMIN, Role.MANAGER)
