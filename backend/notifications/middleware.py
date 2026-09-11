import threading
from contextlib import contextmanager

_thread_locals = threading.local()


def get_current_user():
    user = getattr(_thread_locals, "user", None)
    if user is not None and getattr(user, "is_authenticated", False):
        return user
    return None


@contextmanager
def current_user(user):
    """Temporarily set the acting user (used by signals; handy in tests)."""
    previous = getattr(_thread_locals, "user", None)
    _thread_locals.user = user
    try:
        yield
    finally:
        _thread_locals.user = previous


class CurrentUserMiddleware:
    """Expose the request user to signals via a thread-local."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _thread_locals.user = getattr(request, "user", None)
        try:
            return self.get_response(request)
        finally:
            _thread_locals.user = None
