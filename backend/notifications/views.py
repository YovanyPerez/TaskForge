from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.template.loader import render_to_string
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .models import Notification

RECENT_LIMIT = 8


@login_required
def feed(request):
    qs = (
        Notification.objects.filter(recipient=request.user, is_read=False)
        .select_related("actor", "project", "task")
        .order_by("-created_at")
    )
    html = render_to_string(
        "notifications/partials/notification_items.html",
        {"notifications": qs[:RECENT_LIMIT]},
        request=request,
    )
    return JsonResponse({"count": qs.count(), "html": html})


@require_POST
@login_required
def mark_read(request, pk):
    notification = get_object_or_404(Notification, pk=pk, recipient=request.user)
    if not notification.is_read:
        notification.is_read = True
        notification.save(update_fields=["is_read"])
    return JsonResponse({"ok": True})


@require_POST
@login_required
def mark_all_read(request):
    Notification.objects.filter(recipient=request.user, is_read=False).update(
        is_read=True
    )
    next_url = request.POST.get("next") or "/"
    if not url_has_allowed_host_and_scheme(next_url, allowed_hosts=None):
        next_url = "/"
    return redirect(next_url)
