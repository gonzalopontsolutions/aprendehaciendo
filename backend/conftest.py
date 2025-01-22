import logging
import pytest
import sys
import os
from pathlib import Path
import django

# Obtener la ruta al directorio root del proyecto
ROOT_DIR = Path(__file__).parent.parent
sys.path.append(str(ROOT_DIR))

# Configurar las variables de entorno
os.environ.setdefault("ENVIRONMENT", "development")
from dotenv import load_dotenv

env_file = ROOT_DIR / f'.env.{os.environ["ENVIRONMENT"]}'
load_dotenv(env_file)

# Configurar Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings.development")
django.setup()


# Configuración del logging para los tests
@pytest.fixture(autouse=True)
def setup_logging():
    # Configuración básica
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    # Configurar loggers específicos
    loggers = ["trips.consumers", "trips.services", "tests"]

    for logger_name in loggers:
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.DEBUG)
        logger.propagate = True

    return logging.getLogger("tests")


# Ver los logs incluso cuando la prueba pasa
def pytest_configure(config):
    config.option.log_cli = True
    config.option.log_cli_level = "DEBUG"
