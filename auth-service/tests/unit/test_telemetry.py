import sys
import pathlib
import types
import importlib

SERVICE_SRC = pathlib.Path(__file__).resolve().parents[2] / "src"
PACKAGE_NAME = "authservice"

if PACKAGE_NAME not in sys.modules:
    pkg = types.ModuleType(PACKAGE_NAME)
    pkg.__path__ = [str(SERVICE_SRC)]
    sys.modules[PACKAGE_NAME] = pkg

telemetry = importlib.import_module(f"{PACKAGE_NAME}.telemetry")


def test_create_span_and_attributes():
    span = telemetry.create_span("unit-test-span")
    # OpenTelemetry spans must be explicitly ended to flush processors
    try:
        telemetry.add_span_attributes({"test.attribute": "value"})
    finally:
        # Ensure we end the span even if add_span_attributes failed
        span.end()
    # At this point no assertion is strictly required; absence of exceptions is success 