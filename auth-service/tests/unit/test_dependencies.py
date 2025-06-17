import os
import sys
import types
import pathlib
import importlib
import pytest
from jose import jwt

# --------------------------------------------------------------------------------------
# Helper to load the service modules as a proper Python package so that relative imports
# (e.g. `from .schemas import Token`) inside the service code work during the test run.
# --------------------------------------------------------------------------------------
SERVICE_SRC = pathlib.Path(__file__).resolve().parents[2] / "src"
PACKAGE_NAME = "authservice"

if PACKAGE_NAME not in sys.modules:
    pkg = types.ModuleType(PACKAGE_NAME)
    pkg.__path__ = [str(SERVICE_SRC)]
    sys.modules[PACKAGE_NAME] = pkg

# With the package stubbed out we can perform a regular import which keeps the correct
# __package__ attribute, ensuring that relative imports inside the module resolve.
dependencies = importlib.import_module(f"{PACKAGE_NAME}.dependencies")
schemas = importlib.import_module(f"{PACKAGE_NAME}.schemas")

# -----------------------------------------------------------------------------
# Fixtures & helpers
# -----------------------------------------------------------------------------
@pytest.fixture(autouse=True)
def _set_jwt_secret(monkeypatch):
    """Provide a deterministic JWT secret for every test."""
    monkeypatch.setenv("JWT_SECRET_KEY", "test-secret-key")
    yield

# -----------------------------------------------------------------------------
# Token helpers
# -----------------------------------------------------------------------------

def create_standard_payload():
    return {"sub": "alice@example.com", "user_id": str(123)}

# -----------------------------------------------------------------------------
# Test cases
# -----------------------------------------------------------------------------

def test_create_tokens_structure_and_verification():
    """create_tokens should return a full Token model and both JWTs must validate."""
    token_obj = dependencies.create_tokens(create_standard_payload())

    # Basic structure assertions (Token model from schemas)
    assert isinstance(token_obj, schemas.Token)
    assert token_obj.token_type == "bearer"
    assert token_obj.expires_in == dependencies.get_token_expire_minutes() * 60

    # Access token round-trip
    sub = dependencies.verify_token(token_obj.access_token)
    assert sub == "alice@example.com"

    # Refresh token contains the correct `type` claim
    decoded_refresh = jwt.decode(
        token_obj.refresh_token,
        dependencies.get_jwt_secret_key(),
        algorithms=[dependencies.get_jwt_algorithm()],
    )
    assert decoded_refresh["type"] == "refresh"
    assert decoded_refresh["sub"] == "alice@example.com"


def test_verify_token_invalid_raises():
    """verify_token must raise HTTPException on invalid token input."""
    with pytest.raises(dependencies.HTTPException):
        dependencies.verify_token("not.a.valid.jwt")


def test_verify_refresh_token_type_validation():
    """verify_refresh_token should reject access tokens (missing `type=refresh`)."""
    access_token = dependencies.create_access_token(create_standard_payload())
    with pytest.raises(dependencies.HTTPException):
        async_run(dependencies.verify_refresh_token(access_token))


def async_run(awaitable):
    """Utility to synchronously run a coroutine inside pytest."""
    import asyncio
    return asyncio.get_event_loop().run_until_complete(awaitable)


def test_revoke_and_blacklist(monkeypatch):
    """A revoked token must appear in the in-memory blacklist."""
    token = dependencies.create_access_token(create_standard_payload())
    assert token not in dependencies.revoked_tokens
    dependencies.revoke_token(token)
    assert token in dependencies.revoked_tokens


def test_password_hash_and_verify():
    password = "CorrectHorseBatteryStaple"
    hashed = dependencies.get_password_hash(password)
    assert dependencies.verify_password(password, hashed)
    assert not dependencies.verify_password("wrong-password", hashed)


def test_get_secret_fallback_env(monkeypatch):
    """get_secret must fall back to env vars when Vault is unavailable."""
    monkeypatch.setenv("DATABASE_URL", "postgresql://test:test@localhost/db")
    url = dependencies.get_secret("database/config", "url")
    assert url == "postgresql://test:test@localhost/db" 