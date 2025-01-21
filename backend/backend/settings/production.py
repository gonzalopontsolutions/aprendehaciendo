from .base import *

DEBUG = False
ALLOWED_HOSTS = ['sadasdsad.com', 'www.asdasda.com']

# Configuraciones adicionales de seguridad para producción
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True