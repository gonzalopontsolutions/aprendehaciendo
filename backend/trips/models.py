from django.db import models
from django.conf import settings


class Trip(models.Model):
    ESTADOS = [
        ("pendiente", "Pendiente"),
        ("asignado", "Asignado"),
        ("cancelado", "Cancelado"),
        ("completado", "Completado"),
    ]

    cliente = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="viajes_cliente",
    )
    origen = models.JSONField()  # {'latitud': 12.34, 'longitud': 56.78}
    destino = models.JSONField()  # {'latitud': 12.34, 'longitud': 56.78}
    estado = models.CharField(max_length=15, choices=ESTADOS, default="pendiente")
    conductor_asignado = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="viajes_conductor",
    )
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Viaje {self.id}: {self.cliente} - {self.estado}"


class DriverLocation(models.Model):
    conductor = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="ubicacion"
    )
    latitud = models.FloatField()
    longitud = models.FloatField()
    timestamp = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Ubicación de {self.conductor}: ({self.latitud}, {self.longitud})"
