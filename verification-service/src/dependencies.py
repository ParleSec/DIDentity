import asyncpg
import logging
import hvac
import os
from fastapi import HTTPException
from typing import AsyncGenerator

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Vault client setup
vault_client = hvac.Client(
    url=os.environ.get('VAULT_ADDR', 'http://vault:8200'),
    token=os.environ.get('VAULT_TOKEN', 'root')
)

# Get secrets from Vault
def get_secret(path, key=None):
    try:
        response = vault_client.secrets.kv.v2.read_secret_version(path=path)
        if key:
            return response['data']['data'].get(key)
        return response['data']['data']
    except Exception as e:
        logger.error(f"Error fetching secret from Vault: {str(e)}")
        # In production, fail fast instead of using fallbacks
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve secrets from Vault. Please check Vault configuration."
        )

# Get database URL from Vault
def get_db_url():
    """Get database URL from Vault"""
    try:
        db_config = get_secret('database/config')
        # Construct URL from Vault secrets
        username = db_config.get('username', 'postgres')
        password = db_config.get('password')
        host = db_config.get('host', 'db')
        port = db_config.get('port', '5432')
        database = db_config.get('database', 'decentralized_id')
        
        return f"postgresql://{username}:{password}@{host}:{port}/{database}"
    except Exception as e:
        logger.error(f"Failed to get database URL from Vault: {str(e)}")
        raise

# Database connection
async def get_db_pool() -> AsyncGenerator[asyncpg.Pool, None]:
    try:
        pool = await asyncpg.create_pool(
            get_db_url(),
            min_size=5,
            max_size=20,
            command_timeout=60
        )
        if not pool:
            raise HTTPException(status_code=500, detail="Failed to create database pool")
        try:
            yield pool
        finally:
            if pool:
                await pool.close()
    except asyncpg.InvalidPasswordError:
        logger.error("Database authentication failed")
        raise HTTPException(status_code=500, detail="Database authentication failed")
    except Exception as e:
        logger.error(f"Database connection error: {str(e)}")
        raise HTTPException(status_code=500, detail="Database connection error")