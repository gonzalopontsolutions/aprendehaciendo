import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings.development')
django.setup()

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator, OriginValidator
from django.core.asgi import get_asgi_application
from trips.routing import websocket_urlpatterns
# from .token_auth_middleware import TokenAuthMiddleware

# Configuración del protocolo HTTP
django_asgi_app = get_asgi_application()

# Configuración de la aplicación ASGI
application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": OriginValidator(
        # TokenAuthMiddleware(
            URLRouter(
                websocket_urlpatterns
            ),
        # ),
        ["*"]  # Permite todas las conexiones en desarrollo
    ),
})