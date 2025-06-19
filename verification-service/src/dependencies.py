import asyncpg
import logging
import hvac
import os
import requests
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
        # Use direct HTTP request to ensure correct path
        url = f"{vault_client.url}/v1/kv/data/{path}"
        headers = {"X-Vault-Token": vault_client.token}
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        data = response.json()
        secret_data = data['data']['data']
        
        if key:
            return secret_data.get(key)
        return secret_data
    except Exception as e:
        logger.error(f"Error fetching secret from Vault: {e}, on get {vault_client.url}/v1/kv/data/{path}")
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
        # Fallback to environment variable or default
        return os.environ.get('DATABASE_URL', 'postgresql://postgres:VaultSecureDB2024@db:5432/decentralized_id')

# Global connection pool (reuse across requests)
_db_pool = None

async def get_db_pool():
    """Get or create database connection pool"""
    global _db_pool
    if _db_pool is None:
        try:
            _db_pool = await asyncpg.create_pool(
                get_db_url(),
                min_size=10,
                max_size=50,
                command_timeout=30,
                server_settings={
                    'application_name': 'verification_service',
                    'tcp_keepalives_idle': '600',
                    'tcp_keepalives_interval': '30',
                    'tcp_keepalives_count': '3',
                },
                max_inactive_connection_lifetime=300
            )
            logger.info(f"Database pool created: min=10, max=50")
        except Exception as e:
            logger.error(f"Failed to create database pool: {e}")
            raise HTTPException(status_code=500, detail="Database connection failed")
    
    return _db_pool

# Database connection
async def get_db_connection() -> AsyncGenerator[asyncpg.Connection, None]:
    try:
        pool = await get_db_pool()
        if not pool:
            raise HTTPException(status_code=500, detail="Database pool not available")
        
        async with pool.acquire() as conn:
            yield conn
    except asyncpg.InvalidPasswordError:
        logger.error("Database authentication failed")
        raise HTTPException(status_code=500, detail="Database authentication failed")
    except Exception as e:
        logger.error(f"Database connection error: {str(e)}")
        raise HTTPException(status_code=500, detail="Database connection error")

# Legacy function for backward compatibility  
async def get_db_pool_legacy() -> AsyncGenerator[asyncpg.Pool, None]:
    try:
        pool = await get_db_pool()
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