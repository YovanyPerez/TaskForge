from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.throttling import AnonRateThrottle


class TokenRateThrottle(AnonRateThrottle):
    scope = "token"


class ThrottledObtainAuthToken(ObtainAuthToken):
    """Token endpoint with per-IP rate limiting (on top of django-axes lockout)."""

    throttle_classes = [TokenRateThrottle]
