from .models import Notification


def notifications(request):
    user = getattr(request, "user", None)
    if not (user and user.is_authenticated):
        return {}
    qs = (
        Notification.objects.filter(recipient=user, is_read=False)
        .select_related("actor", "project", "task")
        .order_by("-created_at")
    )
    return {
        "unread_notifications": qs.count(),
        "recent_notifications": list(qs[:8]),
    }
