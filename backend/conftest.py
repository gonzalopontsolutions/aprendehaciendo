import logging
import pytest
import sys


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


# Opcional: Si quieres ver los logs incluso cuando la prueba pasa
def pytest_configure(config):
    config.option.log_cli = True
    config.option.log_cli_level = "DEBUG"
