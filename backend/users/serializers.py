from rest_framework import serializers
from django.contrib.auth.hashers import make_password
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User, Token


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    def create(self, validated_data):
        validated_data["password"] = make_password(validated_data["password"])
        return User.objects.create(**validated_data)

    class Meta:
        model = User
        fields = ["id", "email", "password", "first_name", "last_name", "rol"]


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        # Busca al usuario por email
        user = User.objects.filter(email=data["email"]).first()

        # Verifica si el usuario existe y si la contraseña es correcta
        if user and user.check_password(data["password"]):
            # Genera un refresh token y su correspondiente access token
            refresh = RefreshToken.for_user(user)
            access = str(refresh.access_token)

            # Actualiza o crea el registro en la tabla Token
            Token.objects.update_or_create(
                user=user,
                defaults={
                    "refresh_token": str(refresh),
                    "access_token": access,  # Guardar el access token
                },
            )

            # Incluye el usuario en los datos validados
            return {
                "user": user,  # Agregar el usuario al retorno
                "access": access,
                "refresh": str(refresh),
            }

        # Lanza un error si las credenciales son inválidas
        raise serializers.ValidationError("Invalid credentials.")
