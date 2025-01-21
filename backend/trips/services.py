import logging
from math import radians, sin, cos, sqrt, atan2
from .models import DriverLocation
from django.contrib.auth import get_user_model

# Definir el modelo de usuario
Conductor = get_user_model()

logger = logging.getLogger(__name__)


def calcular_distancia(punto1, punto2):
    """
    Calcula la distancia en kilómetros entre dos puntos usando la fórmula de Haversine.

    Args:
        punto1: Tupla (latitud, longitud) del primer punto
        punto2: Tupla (latitud, longitud) del segundo punto

    Returns:
        float: Distancia en kilómetros
    """
    import math

    lat1, lon1 = punto1
    lat2, lon2 = punto2

    # Radio de la Tierra en kilómetros
    R = 6371.0

    # Convertir latitudes y longitudes de grados a radianes
    lat1 = math.radians(lat1)
    lon1 = math.radians(lon1)
    lat2 = math.radians(lat2)
    lon2 = math.radians(lon2)

    # Diferencias en coordenadas
    dlat = lat2 - lat1
    dlon = lon2 - lon1

    # Fórmula de Haversine
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distancia = R * c

    return round(distancia, 2)


# def asignar_conductor(trip):
#     logger.info(f"Iniciando asignación de conductor para viaje {trip.id}")
#     conductores = DriverLocation.objects.all()
#     logger.info(f"Conductores disponibles: {conductores.count()}")

#     origen = (trip.origen["lat"], trip.origen["lng"])
#     logger.info(f"Origen del viaje: {origen}")

#     distancias = []
#     for ubicacion in conductores:
#         distancia = calcular_distancia(origen, (ubicacion.latitud, ubicacion.longitud))
#         distancias.append((distancia, ubicacion.conductor))
#         logger.info(f"Conductor {ubicacion.conductor.email} a {distancia:.2f} km")

#     distancias.sort(key=lambda x: x[0])

#     if distancias:
#         conductor_seleccionado = distancias[0][1]
#         distancia = distancias[0][0]
#         logger.info(
#             f"""
# === Conductor Seleccionado ===
# ID: {conductor_seleccionado.id}
# Email: {conductor_seleccionado.email}
# Distancia: {distancia:.2f} km
# ============================="""
#         )
#         return conductor_seleccionado
#     else:
#         logger.warning("No hay conductores disponibles")
#         return None


def asignar_conductor(trip, excluir_conductor=None):
    """Asignar el conductor más cercano a un viaje."""
    logger.info(f"Iniciando asignación de conductor para viaje {trip.id}")

    # Obtener conductores disponibles, excluyendo el conductor anterior si existe
    conductores = Conductor.objects.filter(rol="Conductor")
    if excluir_conductor:
        conductores = conductores.exclude(id=excluir_conductor.id)

    logger.info(f"Conductores disponibles: {conductores.count()}")

    if not conductores.exists():
        return None

    origen = (trip.origen["lat"], trip.origen["lng"])
    logger.info(f"Origen del viaje: {origen}")

    # Encontrar el conductor más cercano
    conductor_mas_cercano = None
    menor_distancia = float("inf")

    for conductor in conductores:
        try:
            ubicacion = DriverLocation.objects.get(conductor=conductor)
            punto_conductor = (ubicacion.latitud, ubicacion.longitud)

            distancia = calcular_distancia(origen, punto_conductor)
            logger.info(f"Conductor {conductor.email} a {distancia:.2f} km")

            if distancia < menor_distancia:
                menor_distancia = distancia
                conductor_mas_cercano = conductor

        except DriverLocation.DoesNotExist:
            continue

    if conductor_mas_cercano:
        logger.info(
            f"""
=== Conductor Seleccionado ===
ID: {conductor_mas_cercano.id}
Email: {conductor_mas_cercano.email}
Distancia: {menor_distancia:.2f} km
============================="""
        )

    return conductor_mas_cercano
