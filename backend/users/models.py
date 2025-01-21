from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth.models import AbstractUser


# Modelo base de Usuario
class User(AbstractUser):
    # Ya incluye username, first_name, last_name, email, password, is_staff, is_active, date_joined
    class Role(models.TextChoices):
        ADMINISTRADOR = "Administrador"
        MODERADOR = "Moderador"
        CONDUCTOR = "Conductor"
        PASAJERO = "Pasajero"

    # Eliminar campo username del modelo base
    AbstractUser.username = None

    email = models.EmailField(unique=True, blank=False, null=False)

    # Campos comunes requeridos para todos los usuarios
    rol = models.CharField(max_length=13, choices=Role.choices, default=Role.PASAJERO)

    def __str__(self):
        return f"user: {self.id} - {self.first_name} - {self.last_name}"

    class Meta:
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"


# Modelo para Pasajero
class Pasajero(User):
    rol = User.Role.PASAJERO
    push_token = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"pasajero: {self.id} - {self.first_name} - {self.last_name}"

    class Meta:
        ordering = ["date_joined"]
        verbose_name = "Pasajero"
        verbose_name_plural = "Pasajeros"


# Modelo para Conductor
class Conductor(User):
    rol = User.Role.CONDUCTOR
    push_token = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"conductor: {self.id} - {self.first_name} - {self.last_name}"

    class Meta:
        ordering = ["date_joined"]
        verbose_name = "Conductor"
        verbose_name_plural = "Conductores"


# Modelo para Moderador
class Moderador(User):
    rol = User.Role.MODERADOR

    def __str__(self):
        return f"Moderador: {self.id} - {self.first_name} - {self.last_name}"

    class Meta:
        ordering = ["date_joined"]
        verbose_name = "Moderador"
        verbose_name_plural = "Moderadores"


# Modelo para Administrador
class Administrador(User):
    rol = User.Role.ADMINISTRADOR

    def __str__(self):
        return f"Administrador: {self.id} - {self.first_name} - {self.last_name}"

    class Meta:
        ordering = ["date_joined"]
        verbose_name = "Administrador"
        verbose_name_plural = "Administradores"


class Token(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="personalized_token"
    )
    refresh_token = models.TextField()
    access_token = models.TextField()  # Campo para almacenar el access token
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Token for {self.user.email}"
