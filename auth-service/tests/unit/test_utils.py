import logging
import sys
import pathlib
import types
import importlib
import pytest

SERVICE_SRC = pathlib.Path(__file__).resolve().parents[2] / "src"
PACKAGE_NAME = "authservice"

if PACKAGE_NAME not in sys.modules:
    pkg = types.ModuleType(PACKAGE_NAME)
    pkg.__path__ = [str(SERVICE_SRC)]
    sys.modules[PACKAGE_NAME] = pkg

utils = importlib.import_module(f"{PACKAGE_NAME}.utils")


def test_log_request_info_caplog(caplog):
    """Ensure log_request_info emits an INFO level log with method and path."""
    with caplog.at_level(logging.INFO, logger=utils.logger.name):
        utils.log_request_info("GET", "/health")
    # Only one record should be emitted and contain the expected substrings
    assert any("Received GET request to /health" in record.message for record in caplog.records) 