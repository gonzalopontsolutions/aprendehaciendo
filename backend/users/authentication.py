from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import AuthenticationFailed
from .models import Token


class CustomJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        # Llama al método original de autenticación para validar el token
        response = super().authenticate(request)

        if response is not None:
            user, validated_token = response

            # Obtener el access token en formato de cadena
            access_token_str = str(validated_token)

            # Verificar si el token existe en la base de datos
            if not Token.objects.filter(
                user=user, access_token=access_token_str
            ).exists():
                raise AuthenticationFailed("Token is invalid or user is logged out.")

            return (user, validated_token)

        return None
