from django.utils.translation import gettext_lazy as _
from rest_framework.permissions import SAFE_METHODS, BasePermission


def scope_to_member(queryset, user, **membership_kwargs):
    """Limit a queryset to the user's own resources unless they are admin/manager."""
    if user.is_admin or user.is_manager:
        return queryset
    return queryset.filter(**membership_kwargs)


class IsAdminOrManagerOrReadOnly(BasePermission):
    message = _("Only administrators and managers can modify this resource.")

    def has_permission(self, request, view):
        user = request.user
        if not (user and user.is_authenticated):
            return False
        if request.method in SAFE_METHODS:
            return True
        return user.is_admin or user.is_manager


class IsOwnerOrManager(BasePermission):
    message = _("You can only modify your own content.")

    def has_object_permission(self, request, view, obj):
        user = request.user
        if user.is_admin or user.is_manager:
            return True
        return obj.user_id == user.pk
