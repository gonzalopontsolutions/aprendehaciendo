import json
import asyncio
import logging
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from asgiref.sync import sync_to_async
from .models import Trip, DriverLocation
from .services import asignar_conductor
from channels.db import database_sync_to_async

logger = logging.getLogger(__name__)


class TripConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        user = self.scope["user"]
        logger.info(f"Intento de conexión de usuario: {user}")

        # Verificar autenticación
        if not user.is_authenticated:
            logger.warning("Rechazando conexión - Usuario no autenticado")
            await self.close()
            return

        # Verificar rol
        logger.info(f"Usuario autenticado con ro: {user.rol}")

        # if user.rol == "Conductor":
        #     self.group_name = f"drivers_{user.id}"
        #     await self.channel_layer.group_add("drivers", self.channel_name)
        #     logger.info(f"Conductor {user.id} añadido al grupo 'drivers'")
        #     await self.accept()
        #     return
        if user.rol == "Conductor":
            self.group_name = f"drivers_{user.id}"  # Cambiado de drivers_ a driver_
            await self.channel_layer.group_add(self.group_name, self.channel_name)
            await self.channel_layer.group_add("drivers", self.channel_name)
            logger.info(
                f"Conductor {user.id} añadido a los grupos '{self.group_name}' y 'drivers'"
            )
            await self.accept()
            return
        elif user.rol == "Pasajero":
            self.group_name = f"passenger_{user.id}"
            logger.info(f"Pasajero {user.id} conectado")
            await self.accept()
            return

        logger.warning(f"Rechazando conexión - Rol no válido: {user.rol}")
        await self.close()

    async def disconnect(self, close_code):
        user = self.scope["user"]

        # Remover conductores del grupo
        if user.is_authenticated and user.rol == "Conductor":
            await self.channel_layer.group_discard(
                f"drivers_{user.id}", self.channel_name
            )
            await self.channel_layer.group_discard("drivers", self.channel_name)

    async def receive_json(self, content):
        action = content.get("action")

        # Manejo de acciones recibidas
        if action == "update_location":
            await self.update_driver_location(content)
        elif action == "create_trip":
            await self.create_trip(content)
        elif action == "accept_trip":
            await self.accept_trip(content)
        elif action == "reject_trip":
            await self.reject_trip(content)
        elif action == "notify_trip_assigned":
            await self.notify_trip_assigned(content)

    async def update_driver_location(self, content):
        """Actualizar la ubicación del conductor."""
        lat = content.get("lat")
        lon = content.get("lon")
        user = self.scope["user"]

        if user.is_authenticated and user.rol == "Conductor":
            await sync_to_async(DriverLocation.objects.update_or_create)(
                conductor=user, defaults={"latitud": lat, "longitud": lon}
            )
            await self.send_json({"status": "location_updated"})

    async def create_trip(self, content):
        """Crear un viaje y asignarlo a un conductor."""
        user = self.scope["user"]
        logger.info(f"Creando viaje para pasajero: {user.email}")

        if user.is_authenticated and user.rol == "Pasajero":
            try:
                trip = await sync_to_async(Trip.objects.create)(
                    cliente=user,
                    origen=content.get("origen"),
                    destino=content.get("destino"),
                    estado="pendiente",
                )
                logger.info(f"Viaje creado con ID: {trip.id}")
                await self.assign_trip(trip)
            except Exception as e:
                logger.error(f"Error al crear viaje: {str(e)}")
                await self.send_json({"error": "Error al crear viaje"})

    async def assign_trip(self, trip):
        """Asignar el conductor más cercano a un viaje."""
        try:
            conductor_asignado = await sync_to_async(asignar_conductor)(trip)
            logger.info(f"Conductor seleccionado: {conductor_asignado}")

            if conductor_asignado:
                # Actualizar el viaje
                trip.conductor_asignado = conductor_asignado
                trip.estado = "asignado"
                await sync_to_async(trip.save)()
                logger.info(
                    f"Viaje {trip.id} actualizado con conductor {conductor_asignado.id}"
                )

                # Preparar mensaje de notificación
                message = {
                    "type": "notify_trip_assigned",
                    "trip_id": str(trip.id),
                    "origen": trip.origen,
                    "destino": trip.destino,
                }
                logger.info(
                    f"Enviando mensaje a grupo drivers_{conductor_asignado.id}: {message}"
                )

                # Enviar notificación al conductor
                try:
                    await self.channel_layer.group_send(
                        f"drivers_{conductor_asignado.id}", message
                    )
                    logger.info("Mensaje enviado exitosamente al grupo del conductor")

                    # Iniciar el temporizador de timeout
                    asyncio.create_task(self.check_trip_response_timeout(trip))

                except Exception as e:
                    logger.error(f"Error al enviar mensaje al grupo: {str(e)}")

                # Notificar al pasajero
                await self.send_json(
                    {"status": "trip_assigned", "driver_id": conductor_asignado.id}
                )
            else:
                logger.warning("No hay conductores disponibles")
                await self.send_json({"status": "no_drivers_available"})

        except Exception as e:
            logger.error(f"Error en assign_trip: {str(e)}")
            await self.send_json({"error": "Error al asignar conductor"})

    # async def assign_trip(self, trip):
    #     """Asignar el conductor más cercano a un viaje."""
    #     try:
    #         conductor_asignado = await sync_to_async(asignar_conductor)(trip)
    #         logger.info(f"Conductor seleccionado: {conductor_asignado}")

    #         if conductor_asignado:
    #             # Actualizar el viaje
    #             trip.conductor_asignado = conductor_asignado
    #             trip.estado = "asignado"
    #             await sync_to_async(trip.save)()
    #             logger.info(
    #                 f"Viaje {trip.id} actualizado con conductor {conductor_asignado.id}"
    #             )

    #             # Preparar mensaje de notificación
    #             message = {
    #                 "type": "notify_trip_assigned",
    #                 "trip_id": str(trip.id),
    #                 "origen": trip.origen,
    #                 "destino": trip.destino,
    #             }
    #             logger.info(
    #                 f"Enviando mensaje a grupo drivers_{conductor_asignado.id}: {message}"
    #             )

    #             # Enviar notificación al conductor
    #             try:
    #                 await self.channel_layer.group_send(
    #                     f"drivers_{conductor_asignado.id}", message
    #                 )
    #                 logger.info("Mensaje enviado exitosamente al grupo del conductor")
    #             except Exception as e:
    #                 logger.error(f"Error al enviar mensaje al grupo: {str(e)}")

    #             # Notificar al pasajero
    #             await self.send_json(
    #                 {"status": "trip_assigned", "driver_id": conductor_asignado.id}
    #             )
    #         else:
    #             logger.warning("No hay conductores disponibles")
    #             await self.send_json({"status": "no_drivers_available"})

    #     except Exception as e:
    #         logger.error(f"Error en assign_trip: {str(e)}")
    #         await self.send_json({"error": "Error al asignar conductor"})

    async def notify_trip_assigned(self, event):
        """Manejador para notificar al conductor sobre un viaje asignado."""
        logger.info(f"Ejecutando notify_trip_assigned con evento: {event}")
        try:
            await self.send_json(
                {
                    "type": "trip_assigned",
                    "trip_id": event["trip_id"],
                    "origen": event["origen"],
                    "destino": event["destino"],
                }
            )
            logger.info("Notificación enviada exitosamente al conductor")
        except Exception as e:
            logger.error(f"Error en notify_trip_assigned: {str(e)}")

    async def accept_trip(self, content):
        """El conductor acepta el viaje."""
        trip_id = content.get("trip_id")
        user = self.scope["user"]

        if user.is_authenticated and user.rol == "Conductor":
            try:
                trip = await sync_to_async(Trip.objects.get)(id=trip_id)
                if trip.conductor_asignado == user and trip.estado == "asignado":
                    trip.estado = "aceptado"  # Cambiado de 'pendiente' a 'aceptado'
                    await sync_to_async(trip.save)()
                    logger.info(f"Viaje {trip_id} aceptado por conductor {user.id}")
                    await self.send_json({"status": "trip_accepted"})
            except Trip.DoesNotExist:
                logger.error(f"Viaje {trip_id} no encontrado")

    async def reject_trip(self, content):
        """El conductor rechaza el viaje."""
        trip_id = content.get("trip_id")
        user = self.scope["user"]

        if user.is_authenticated and user.rol == "Conductor":
            trip = await sync_to_async(Trip.objects.get)(id=trip_id)
            if trip.conductor_asignado == user and trip.estado == "asignado":
                trip.conductor_asignado = None
                trip.estado = "pendiente"
                await sync_to_async(trip.save)()

                # Reasignar el viaje a otro conductor
                await self.assign_trip(trip)

    async def trip_assigned(self, event):
        """Notificar a los conductores sobre un viaje asignado."""
        await self.send_json(
            {
                "type": "trip_assigned",
                "trip_id": event["trip_id"],
                "origen": event["origen"],
                "destino": event["destino"],
            }
        )

    async def check_trip_response_timeout(self, trip):
        """Verificar si el conductor responde en el tiempo límite."""
        logger.info(f"Iniciando temporizador de timeout para viaje {trip.id}")
        try:
            await asyncio.sleep(30)  # Esperar 30 segundos

            # Recargar el viaje desde la base de datos usando select_related
            trip = await database_sync_to_async(
                lambda: Trip.objects.select_related("conductor_asignado").get(
                    id=trip.id
                )
            )()
            logger.info(f"Verificando estado del viaje {trip.id} después de timeout")

            if trip.estado == "asignado":
                logger.info(f"Timeout alcanzado para viaje {trip.id}. Reasignando...")

                # Guardar referencia al conductor anterior
                conductor_anterior = trip.conductor_asignado

                # Resetear el viaje
                trip.conductor_asignado = None
                trip.estado = "pendiente"
                await database_sync_to_async(trip.save)()

                # Notificar al conductor anterior que perdió el viaje
                if conductor_anterior:
                    await self.channel_layer.group_send(
                        f"drivers_{conductor_anterior.id}",
                        {"type": "notify_trip_timeout", "trip_id": str(trip.id)},
                    )

                # Intentar reasignar el viaje excluyendo al conductor anterior
                logger.info("Intentando reasignar el viaje...")
                conductor_asignado = await database_sync_to_async(
                    lambda: asignar_conductor(
                        trip, excluir_conductor=conductor_anterior
                    )
                )()

                if conductor_asignado:
                    trip.conductor_asignado = conductor_asignado
                    trip.estado = "asignado"
                    await database_sync_to_async(trip.save)()

                    # Enviar notificación al nuevo conductor
                    await self.channel_layer.group_send(
                        f"drivers_{conductor_asignado.id}",
                        {
                            "type": "notify_trip_assigned",
                            "trip_id": str(trip.id),
                            "origen": trip.origen,
                            "destino": trip.destino,
                        },
                    )

        except Exception as e:
            logger.error(f"Error en check_trip_response_timeout: {str(e)}")
            logger.exception("Traceback completo:")

    async def notify_trip_timeout(self, event):
        """Notificar al conductor que perdió el viaje por timeout."""
        await self.send_json(
            {
                "type": "trip_timeout",
                "trip_id": event["trip_id"],
                "message": "Viaje reasignado por falta de respuesta",
            }
        )
