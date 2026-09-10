from django.utils import translation


class UserLanguageMiddleware:
    """Activate the logged-in user's preferred language, if set."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, "user", None)
        if getattr(user, "is_authenticated", False):
            language = getattr(user, "language", "") or ""
            if language:
                translation.activate(language)
                request.LANGUAGE_CODE = language
        return self.get_response(request)
