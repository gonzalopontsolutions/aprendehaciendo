import pytest
import logging
from channels.testing import WebsocketCommunicator
from channels.db import database_sync_to_async
from channels.routing import URLRouter
from django.urls import re_path
from asgiref.sync import sync_to_async
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from backend.asgi import application
from trips.models import Trip, DriverLocation
from users.models import Conductor, Pasajero
from trips.consumers import TripConsumer
import json
import asyncio

# Configurar logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

pytestmark = pytest.mark.django_db


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
class TestWebSocketConnections:
    async def test_conductor_conexion_exitosa(self):
        """Verifica que un conductor puede conectarse exitosamente al WebSocket."""
        try:
            # Crear un usuario conductor
            conductor = await database_sync_to_async(Conductor.objects.create_user)(
                username="conductor",
                email="conductor@test.com",
                password="testpassword",
                rol="Conductor",
            )

            # Crear application específica para testing
            application = URLRouter(
                [
                    re_path(r"^ws/trip/$", TripConsumer.as_asgi()),
                ]
            )

            # Iniciar conexión WebSocket con timeout aumentado
            communicator = WebsocketCommunicator(
                application=application,
                path="/ws/trip/",
                headers=[(b"origin", b"http://localhost")],
            )
            communicator.scope["user"] = conductor

            # Intentar conectar con un timeout más largo (10 segundos)
            connected, subprotocol = await communicator.connect(timeout=10)

            # Verificar conexión exitosa
            assert connected, "La conexión WebSocket no pudo establecerse"

        except Exception as e:
            pytest.fail(f"Error durante la prueba: {str(e)}")

        finally:
            # Limpiar
            if "communicator" in locals():
                await communicator.disconnect()
            if "conductor" in locals():
                await database_sync_to_async(conductor.delete)()

    @pytest.mark.django_db(transaction=True)
    async def test_conductor_sin_autenticar(self):
        """Verifica que un usuario sin autenticar no puede conectarse."""
        application = URLRouter(
            [
                re_path(r"^ws/trip/$", TripConsumer.as_asgi()),
            ]
        )

        communicator = WebsocketCommunicator(
            application=application,
            path="/ws/trip/",
            headers=[(b"origin", b"http://localhost")],
        )
        communicator.scope["user"] = AnonymousUser()

        connected, _ = await communicator.connect(timeout=10)
        assert not connected

        await communicator.disconnect()

    async def test_actualizacion_ubicacion_conductor(self):
        """Verifica que un conductor puede enviar actualizaciones de ubicación."""
        try:
            # Crear conductor
            conductor = await database_sync_to_async(Conductor.objects.create_user)(
                username="conductor_ubicacion",
                email="conductor_ubicacion@test.com",
                password="testpassword",
                rol="Conductor",
            )
            logger.debug(f"Conductor creado: {conductor.username}")

            # Configurar aplicación
            application = URLRouter(
                [
                    re_path(r"^ws/trip/$", TripConsumer.as_asgi()),
                ]
            )

            # Crear communicator
            communicator = WebsocketCommunicator(
                application=application,
                path="/ws/trip/",
                headers=[(b"origin", b"http://127.0.0.1")],
            )
            communicator.scope["user"] = conductor

            # Conectar
            logger.debug("Intentando conectar al WebSocket...")
            connected, _ = await communicator.connect(timeout=10)
            assert connected, "No se pudo establecer la conexión WebSocket"
            logger.debug("Conexión WebSocket establecida exitosamente")

            # Preparar datos de ubicación
            ubicacion_data = {
                "action": "update_location",
                "lat": 4.6097100,
                "lon": -74.0817500,
            }

            # Enviar actualización de ubicación
            logger.debug(f"Enviando datos de ubicación: {ubicacion_data}")
            await communicator.send_json_to(ubicacion_data)

            # Esperar y verificar la respuesta
            try:
                logger.debug("Esperando respuesta del WebSocket...")
                response = await communicator.receive_json_from(timeout=2)
                logger.debug(f"Respuesta recibida: {response}")
                assert response["status"] == "location_updated"

                # Verificar la base de datos
                logger.debug("Verificando actualización en la base de datos...")
                await asyncio.sleep(1)  # Dar tiempo para que se guarde en la DB

                # Obtener la ubicación del conductor de forma asíncrona
                driver_location = await database_sync_to_async(
                    lambda: DriverLocation.objects.filter(conductor=conductor).first()
                )()

                assert (
                    driver_location is not None
                ), "No se encontró la ubicación en la base de datos"
                assert float(driver_location.latitud) == ubicacion_data["lat"]
                assert float(driver_location.longitud) == ubicacion_data["lon"]
                logger.debug("Verificación de base de datos exitosa")

            except asyncio.TimeoutError:
                logger.error("Timeout esperando respuesta del WebSocket")
                # Verificar si hay mensajes pendientes
                while True:
                    try:
                        message = await communicator.receive_from(timeout=0.1)
                        logger.debug(f"Mensaje pendiente encontrado: {message}")
                    except asyncio.TimeoutError:
                        break
                raise

        except Exception as e:
            logger.error(f"Error durante la prueba: {str(e)}")
            raise

        finally:
            # Limpiar
            logger.debug("Limpiando recursos...")
            if "communicator" in locals():
                await communicator.disconnect()
            if "conductor" in locals():
                await database_sync_to_async(conductor.delete)()
            logger.debug("Limpieza completada")

    async def test_asignacion_viaje(self):
        """Verifica que el sistema asigna el viaje al conductor más cercano."""
        try:
            logger.info("\n=== Iniciando prueba de asignación de viaje ===")

            # Crear conductor y su ubicación
            conductor = await database_sync_to_async(Conductor.objects.create_user)(
                username="conductor_test",
                email="conductor@test.com",
                password="testpassword",
                rol="Conductor",
            )
            logger.info(
                f"✓ Conductor creado - ID: {conductor.id}, Email: {conductor.email}"
            )

            ubicacion = await database_sync_to_async(DriverLocation.objects.create)(
                conductor=conductor, latitud=4.6097100, longitud=-74.0817500
            )
            logger.info(
                f"✓ Ubicación registrada - Lat: {ubicacion.latitud}, Lon: {ubicacion.longitud}"
            )

            # Crear pasajero
            pasajero = await database_sync_to_async(Pasajero.objects.create_user)(
                username="pasajero_test",
                email="pasajero@test.com",
                password="testpassword",
                rol="Pasajero",
            )
            logger.info(
                f"✓ Pasajero creado - ID: {pasajero.id}, Email: {pasajero.email}"
            )

            # Configurar aplicación
            application = URLRouter(
                [
                    re_path(r"^ws/trip/$", TripConsumer.as_asgi()),
                ]
            )

            # Conectar conductor
            logger.info("\n=== Conectando conductor al WebSocket ===")
            conductor_ws = WebsocketCommunicator(
                application=application,
                path="/ws/trip/",
                headers=[(b"origin", b"http://localhost")],
            )
            conductor_ws.scope["user"] = conductor
            connected, _ = await conductor_ws.connect()
            assert connected, "El conductor no pudo conectarse"
            logger.info("✓ Conductor conectado al WebSocket")

            # Conectar pasajero
            logger.info("\n=== Conectando pasajero al WebSocket ===")
            pasajero_ws = WebsocketCommunicator(
                application=application,
                path="/ws/trip/",
                headers=[(b"origin", b"http://localhost")],
            )
            pasajero_ws.scope["user"] = pasajero
            connected, _ = await pasajero_ws.connect()
            assert connected, "El pasajero no pudo conectarse"
            logger.info("✓ Pasajero conectado al WebSocket")

            # Crear solicitud de viaje
            logger.info("\n=== Enviando solicitud de viaje ===")
            solicitud_viaje = {
                "action": "create_trip",
                "origen": {"lat": 4.6097100, "lng": -74.0817500},
                "destino": {"lat": 4.6297100, "lng": -74.0647500},
            }
            logger.info(f"Datos de la solicitud: {solicitud_viaje}")
            await pasajero_ws.send_json_to(solicitud_viaje)
            logger.info("✓ Solicitud enviada")

            # Esperar respuesta del pasajero
            logger.info("\n=== Esperando respuesta para el pasajero ===")
            try:
                pasajero_response = await pasajero_ws.receive_json_from(timeout=2)
                logger.info(f"Respuesta recibida por el pasajero: {pasajero_response}")
            except asyncio.TimeoutError:
                logger.error("❌ Timeout esperando respuesta del pasajero")

            # Esperar la notificación del conductor
            logger.info("\n=== Esperando notificación para el conductor ===")
            try:
                response = await conductor_ws.receive_json_from(timeout=2)
                logger.info(f"Respuesta recibida por el conductor: {response}")
                assert (
                    response["type"] == "trip_assigned"
                ), "Tipo de respuesta incorrecto"
                assert "trip_id" in response, "No se recibió ID del viaje"
            except asyncio.TimeoutError:
                logger.error("❌ Timeout esperando la asignación del viaje")
                # Verificar el estado del viaje en la base de datos
                trip = await database_sync_to_async(
                    lambda: Trip.objects.select_related(
                        "conductor_asignado", "cliente"
                    ).first()
                )()
                if trip:
                    logger.error(
                        f"""
                        Estado del viaje en DB:
                        ID: {trip.id}
                        Estado: {trip.estado}
                        Conductor: {trip.conductor_asignado.email if trip.conductor_asignado else 'None'}
                        Cliente: {trip.cliente.email}"""
                    )
                raise

        except Exception as e:
            logger.error(f"❌ Error durante la prueba: {str(e)}")
            raise

        finally:
            logger.info("\n=== Limpiando recursos ===")
            if "conductor_ws" in locals():
                await conductor_ws.disconnect()
            if "pasajero_ws" in locals():
                await pasajero_ws.disconnect()
            if "conductor" in locals():
                await database_sync_to_async(conductor.delete)()
            if "pasajero" in locals():
                await database_sync_to_async(pasajero.delete)()
            logger.info("✓ Limpieza completada")

    async def test_timeout_asignacion_viaje(self):
        """Verifica que el sistema reasigna el viaje si el conductor no responde en 30 segundos."""
        try:
            logger.info("\n=== Iniciando prueba de timeout en asignación de viaje ===")

            # Crear dos conductores y sus ubicaciones
            conductor1 = await database_sync_to_async(Conductor.objects.create_user)(
                username="conductor_test1",
                email="conductor1@test.com",
                password="testpassword",
                rol="Conductor",
            )
            logger.info(
                f"✓ Conductor 1 creado - ID: {conductor1.id}, Email: {conductor1.email}"
            )

            conductor2 = await database_sync_to_async(Conductor.objects.create_user)(
                username="conductor_test2",
                email="conductor2@test.com",
                password="testpassword",
                rol="Conductor",
            )
            logger.info(
                f"✓ Conductor 2 creado - ID: {conductor2.id}, Email: {conductor2.email}"
            )

            # Ubicar conductor1 más cerca del origen
            ubicacion1 = await database_sync_to_async(DriverLocation.objects.create)(
                conductor=conductor1, latitud=4.6097100, longitud=-74.0817500
            )
            logger.info(
                f"✓ Ubicación conductor 1 registrada - Lat: {ubicacion1.latitud}, Lon: {ubicacion1.longitud}"
            )

            # Ubicar conductor2 un poco más lejos
            ubicacion2 = await database_sync_to_async(DriverLocation.objects.create)(
                conductor=conductor2, latitud=4.6197100, longitud=-74.0917500
            )
            logger.info(
                f"✓ Ubicación conductor 2 registrada - Lat: {ubicacion2.latitud}, Lon: {ubicacion2.longitud}"
            )

            # Crear pasajero
            pasajero = await database_sync_to_async(Pasajero.objects.create_user)(
                username="pasajero_test",
                email="pasajero@test.com",
                password="testpassword",
                rol="Pasajero",
            )
            logger.info(
                f"✓ Pasajero creado - ID: {pasajero.id}, Email: {pasajero.email}"
            )

            # Configurar aplicación
            application = URLRouter(
                [
                    re_path(r"^ws/trip/$", TripConsumer.as_asgi()),
                ]
            )

            # Conectar conductores
            logger.info("\n=== Conectando conductores al WebSocket ===")
            conductor1_ws = WebsocketCommunicator(
                application=application,
                path="/ws/trip/",
                headers=[(b"origin", b"http://localhost")],
            )
            conductor1_ws.scope["user"] = conductor1
            connected, _ = await conductor1_ws.connect()
            assert connected, "El conductor 1 no pudo conectarse"
            logger.info("✓ Conductor 1 conectado al WebSocket")

            conductor2_ws = WebsocketCommunicator(
                application=application,
                path="/ws/trip/",
                headers=[(b"origin", b"http://localhost")],
            )
            conductor2_ws.scope["user"] = conductor2
            connected, _ = await conductor2_ws.connect()
            assert connected, "El conductor 2 no pudo conectarse"
            logger.info("✓ Conductor 2 conectado al WebSocket")

            # Conectar pasajero
            logger.info("\n=== Conectando pasajero al WebSocket ===")
            pasajero_ws = WebsocketCommunicator(
                application=application,
                path="/ws/trip/",
                headers=[(b"origin", b"http://localhost")],
            )
            pasajero_ws.scope["user"] = pasajero
            connected, _ = await pasajero_ws.connect()
            assert connected, "El pasajero no pudo conectarse"
            logger.info("✓ Pasajero conectado al WebSocket")

            # Crear solicitud de viaje
            logger.info("\n=== Enviando solicitud de viaje ===")
            solicitud_viaje = {
                "action": "create_trip",
                "origen": {"lat": 4.6097100, "lng": -74.0817500},
                "destino": {"lat": 4.6297100, "lng": -74.0647500},
            }
            await pasajero_ws.send_json_to(solicitud_viaje)
            logger.info("✓ Solicitud enviada")

            # Verificar que el viaje se asigna primero al conductor más cercano
            logger.info("\n=== Verificando asignación inicial al conductor 1 ===")
            response1 = await conductor1_ws.receive_json_from(timeout=2)
            assert response1["type"] == "trip_assigned", "Tipo de respuesta incorrecto"
            trip_id = response1["trip_id"]
            logger.info(f"✓ Viaje {trip_id} asignado inicialmente al conductor 1")

            # Esperar a que pase el timeout (reducimos el tiempo para el test)
            logger.info("\n=== Esperando timeout de asignación ===")
            # Aquí podríamos modificar el tiempo de espera para el test
            await asyncio.sleep(32)  # 32 segundos para asegurar que pase el timeout

            # Verificar que el viaje se reasigna al segundo conductor
            logger.info("\n=== Verificando reasignación al conductor 2 ===")
            response2 = await conductor2_ws.receive_json_from(timeout=2)
            assert response2["type"] == "trip_assigned", "Tipo de respuesta incorrecto"
            assert response2["trip_id"] == trip_id, "ID de viaje incorrecto"
            logger.info(f"✓ Viaje {trip_id} reasignado al conductor 2")

            # Verificar el estado final en la base de datos
            trip = await database_sync_to_async(
                lambda: Trip.objects.select_related(
                    "conductor_asignado", "cliente"
                ).get(id=trip_id)
            )()
            assert (
                trip.conductor_asignado.id == conductor2.id
            ), f"Conductor final incorrecto. Esperado: {conductor2.id}, Actual: {trip.conductor_asignado.id}"
            logger.info("✓ Estado final del viaje verificado en la base de datos")

        except Exception as e:
            logger.error(f"❌ Error durante la prueba: {str(e)}")
            raise

        finally:
            logger.info("\n=== Limpiando recursos ===")
            # Desconectar WebSockets
            if "conductor1_ws" in locals():
                await conductor1_ws.disconnect()
            if "conductor2_ws" in locals():
                await conductor2_ws.disconnect()
            if "pasajero_ws" in locals():
                await pasajero_ws.disconnect()

            # Eliminar usuarios
            if "conductor1" in locals():
                await database_sync_to_async(conductor1.delete)()
            if "conductor2" in locals():
                await database_sync_to_async(conductor2.delete)()
            if "pasajero" in locals():
                await database_sync_to_async(pasajero.delete)()

            logger.info("✓ Limpieza completada")
