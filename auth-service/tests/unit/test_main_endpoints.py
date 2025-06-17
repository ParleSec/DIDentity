import sys
import types
import pathlib
import importlib
from fastapi.testclient import TestClient

SRC_ROOT = pathlib.Path(__file__).resolve().parents[2] / "src"
PKG_NAME = "authservice"

if PKG_NAME not in sys.modules:
    pkg = types.ModuleType(PKG_NAME)
    pkg.__path__ = [str(SRC_ROOT.parent)]
    sys.modules[PKG_NAME] = pkg

main = importlib.import_module(f"{PKG_NAME}.main")
app = main.app
client = TestClient(app)


def test_test_endpoint():
    r = client.get("/test")
    assert r.status_code == 200
    assert r.json()["message"].startswith("Auth service is running")


def test_sdk_endpoint_valid():
    r = client.get("/sdk/python")
    assert r.status_code == 200
    body = r.json()
    assert body["message"].startswith("SDK for python")


def test_sdk_endpoint_invalid():
    r = client.get("/sdk/rust")
    assert r.status_code == 400 