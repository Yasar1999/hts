from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken


class CustomJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        try:
            return super().authenticate(request)
        except TokenError as e:
            raise AuthenticationFailed(f"Token error: {str(e)}")
        except InvalidToken as e:
            raise AuthenticationFailed("Token is invalid or expired")
