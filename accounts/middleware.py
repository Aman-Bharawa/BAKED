from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser

from .jwt_utils import decode_jwt


class JWTAuthenticationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not getattr(request, "user", None) or not request.user.is_authenticated:
            token = request.COOKIES.get("auth_token")
            if token:
                payload = decode_jwt(token)
                if payload:
                    user_model = get_user_model()
                    try:
                        request.user = user_model.objects.get(id=payload["user_id"])
                    except user_model.DoesNotExist:
                        request.user = AnonymousUser()

        return self.get_response(request)
