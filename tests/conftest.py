import pytest
import asyncpg
import asyncio
from fastapi.testclient import TestClient
from typing import Generator, Dict
import jwt
from datetime import datetime, timedelta

# Test database configuration
TEST_DATABASE_URL = "postgresql://postgres:password@localhost:5432/test_decentralized_id"

# Test constants
TEST_SECRET_KEY = "test_secret_key"
TEST_ALGORITHM = "HS256"

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def test_db_pool():
    pool = await asyncpg.create_pool(TEST_DATABASE_URL)
    yield pool
    await pool.close()

@pytest.fixture(scope="function")
async def clean_db(test_db_pool):
    async with test_db_pool.acquire() as conn:
        await conn.execute("TRUNCATE users, dids, credentials CASCADE")
    yield

@pytest.fixture
def test_user() -> Dict:
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password": "TestPassword123"
    }

@pytest.fixture
def test_token(test_user) -> str:
    payload = {
        "sub": test_user["email"],
        "exp": datetime.utcnow() + timedelta(minutes=30)
    }
    return jwt.encode(payload, TEST_SECRET_KEY, algorithm=TEST_ALGORITHM)

# Service client fixtures
@pytest.fixture
def auth_client() -> Generator:
    from auth_service.main import app
    with TestClient(app) as client:
        yield client

@pytest.fixture
def did_client() -> Generator:
    from did_service.main import app
    with TestClient(app) as client:
        yield client

@pytest.fixture
def credential_client() -> Generator:
    from credential_service.main import app
    with TestClient(app) as client:
        yield client

@pytest.fixture
def verification_client() -> Generator:
    from verification_service.main import app
    with TestClient(app) as client:
        yield client