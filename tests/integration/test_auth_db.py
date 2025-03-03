import pytest
from auth_service.src.dependencies import get_db_pool

@pytest.mark.asyncio
async def test_user_creation_and_retrieval(test_db_pool, clean_db, test_user):
    async with test_db_pool.acquire() as conn:
        # Create user
        user_id = await conn.fetchval(
            """
            INSERT INTO users (username, email, password_hash)
            VALUES ($1, $2, $3)
            RETURNING id
            """,
            test_user["username"],
            test_user["email"],
            "hashed_password"
        )
        assert user_id is not None

        # Retrieve user
        user = await conn.fetchrow(
            "SELECT * FROM users WHERE email = $1",
            test_user["email"]
        )
        assert user["username"] == test_user["username"]