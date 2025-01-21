from .base import *

DEBUG = False

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': get_env_value('DB_NAME'),
        'USER': get_env_value('DB_USER'),
        'PASSWORD': get_env_value('DB_PASSWORD'),
        'HOST': get_env_value('DB_HOST'),
        'PORT': get_env_value('DB_PORT'),
    }
}

# Allowed hosts
ALLOWED_HOSTS = [get_env_value('ALLOWED_HOSTS').split(',')]

# CORS settings
CORS_ALLOWED_ORIGINS = get_env_value('CORS_ALLOWED_ORIGINS').split(',')
CORS_ALLOW_ALL_ORIGINS = False

# Email configuration - Using staging email service or sandbox
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = get_env_value('EMAIL_HOST')
EMAIL_PORT = int(get_env_value('EMAIL_PORT'))
EMAIL_USE_TLS = True
EMAIL_HOST_USER = get_env_value('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = get_env_value('EMAIL_HOST_PASSWORD')

# Cache settings
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': get_env_value('REDIS_URL'),
    }
}

# Static files settings
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Security settings for staging (similar to production but slightly relaxed)
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# Logging configuration for staging
LOGGING['handlers']['file'] = {
    'level': 'WARNING',
    'class': 'logging.FileHandler',
    'filename': BASE_DIR / 'logs' / 'django.log',
    'formatter': 'verbose',
}

LOGGING['loggers']['django']['handlers'].append('file')
LOGGING['loggers']['django']['level'] = 'WARNING'