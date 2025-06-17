import types
import sys
import pathlib
import types as _types
import importlib
import pytest

SERVICE_SRC = pathlib.Path(__file__).resolve().parents[2] / "src"
PACKAGE_NAME = "authservice"

if PACKAGE_NAME not in sys.modules:
    pkg = types.ModuleType(PACKAGE_NAME)
    pkg.__path__ = [str(SERVICE_SRC.parent)]
    sys.modules[PACKAGE_NAME] = pkg

messaging = importlib.import_module(f"{PACKAGE_NAME}.messaging")

class DummyChannel:
    """Minimal stub for pika channel used in tests."""

    def __init__(self):
        self.published = []
        self.exchange_declared = False

    # The real method signature takes many params but we only need routing_key & body
    def basic_publish(self, exchange, routing_key, body, properties=None):
        self.published.append((exchange, routing_key, body))

    def exchange_declare(self, *args, **kwargs):
        self.exchange_declared = True

    def queue_declare(self, **kwargs):
        return None

    def queue_bind(self, **kwargs):
        return None

    def basic_consume(self, **kwargs):
        return None

    def basic_ack(self, **kwargs):
        return None

    def basic_nack(self, **kwargs):
        return None

    def start_consuming(self):
        return None


def test_publish_with_stubbed_channel(monkeypatch):
    bus = messaging.EventBus()

    dummy_channel = DummyChannel()
    dummy_connection = _types.SimpleNamespace(is_closed=False)

    # Monkeypatch connect so it simply installs our dummy channel/conn and returns True
    async def fake_connect(self):
        self.connection = dummy_connection
        self.channel = dummy_channel
        return True

    monkeypatch.setattr(messaging.EventBus, "connect", fake_connect, raising=True)

    # Ensure internal instance uses our fake connect
    monkeypatch.setattr(bus, "channel", dummy_channel, raising=False)
    monkeypatch.setattr(bus, "connection", dummy_connection, raising=False)

    # Now publish an event
    import asyncio
    asyncio.run(
        bus.publish("user.created", {"id": "123"})
    )

    assert dummy_channel.published  # Something was published
    exchange, routing_key, body = dummy_channel.published[0]
    assert exchange == bus.exchange_name
    assert routing_key == "user.created" 