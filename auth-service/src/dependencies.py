import asyncpg
import logging
import os
import uuid
import sys
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from typing import Optional, Dict, List
from fastapi import Depends, HTTPException, status

# Add vault directory to Python path
sys.path.append('/app/vault')

try:
    from vault_client import VaultClient, VaultClientError
    vault_client = VaultClient()
    VAULT_AVAILABLE = True
except ImportError:
    logging.warning("Vault client not available, using fallback configuration")
    VAULT_AVAILABLE = False

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Get secrets from Vault with fallback
def get_secret(path, key=None):
    """Get secret from Vault with fallback to environment variables"""
    if VAULT_AVAILABLE:
        try:
            return vault_client.get_secret(path, key)
        except VaultClientError as e:
            logger.error(f"Error fetching secret from Vault: {e}")
    
    # Fallback to environment variables or defaults
    if path == 'database/config':
        if key == 'url':
            return os.environ.get('DATABASE_URL', 'postgresql://postgres:password@db:5432/decentralized_id')
        elif key == 'username':
            return os.environ.get('DB_USERNAME', 'postgres')
        elif key == 'password':
            return os.environ.get('DB_PASSWORD', 'password')
        elif key == 'host':
            return os.environ.get('DB_HOST', 'db')
        elif key == 'port':
            return os.environ.get('DB_PORT', '5432')
        elif key == 'database':
            return os.environ.get('DB_NAME', 'decentralized_id')
    elif path == 'auth/jwt':
        if key == 'secret_key':
            return os.environ.get('JWT_SECRET_KEY', 'fallback-secret-key')
        elif key == 'algorithm':
            return os.environ.get('JWT_ALGORITHM', 'HS256')
        elif key == 'token_expire_minutes':
            return int(os.environ.get('JWT_EXPIRE_MINUTES', '30'))
        elif key == 'refresh_token_expire_days':
            return int(os.environ.get('JWT_REFRESH_EXPIRE_DAYS', '7'))
    
    raise HTTPException(
        status_code=500,
        detail=f"Failed to retrieve secret: {path}/{key}"
    )

# Constants from Vault
def get_db_url():
    """Get database URL from Vault or environment"""
    if VAULT_AVAILABLE:
        try:
            return vault_client.get_database_url()
        except VaultClientError as e:
            logger.error(f"Failed to get database URL from Vault: {str(e)}")
    
    # Fallback to environment variable
    return os.environ.get('DATABASE_URL', 'postgresql://postgres:VaultSecureDB2024@db:5432/decentralized_id')

def get_jwt_secret_key():
    """Get JWT secret key from Vault or environment"""
    if VAULT_AVAILABLE:
        try:
            return vault_client.get_jwt_secret_key()
        except VaultClientError as e:
            logger.error(f"Failed to get JWT secret from Vault: {str(e)}")
    
    # Fallback to environment variable
    return os.environ.get('JWT_SECRET_KEY', 'fallback-secret-key')

def get_jwt_algorithm():
    """Get JWT algorithm from Vault or environment"""
    try:
        return get_secret('auth/jwt', 'algorithm')
    except:
        return 'HS256'

def get_token_expire_minutes():
    """Get token expiration time from Vault or environment"""
    try:
        return int(get_secret('auth/jwt', 'token_expire_minutes'))
    except:
        return 30

def get_refresh_token_expire_days():
    """Get refresh token expiration time from Vault or environment"""
    try:
        return int(get_secret('auth/jwt', 'refresh_token_expire_days'))
    except:
        return 7

# Security
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# In-memory blacklist for revoked tokens (in production, use Redis or a database)
# This is a simple implementation - for production, use a persistent store
revoked_tokens = set()

# Global connection pool (reuse across requests)
_db_pool = None
_redis_client = None

async def get_db_pool():
    """Get or create database connection pool"""
    global _db_pool
    if _db_pool is None:
        try:
            _db_pool = await asyncpg.create_pool(
                get_db_url(),
                min_size=10,  # Increased minimum connections
                max_size=50,  # Increased maximum connections
                command_timeout=30,  # Reduced timeout
                server_settings={
                    'application_name': 'auth_service',
                    'tcp_keepalives_idle': '600',
                    'tcp_keepalives_interval': '30',
                    'tcp_keepalives_count': '3',
                },
                max_inactive_connection_lifetime=300  # 5 minutes
            )
            logger.info(f"Database pool created: min=10, max=50")
        except Exception as e:
            logger.error(f"Failed to create database pool: {e}")
            raise HTTPException(status_code=500, detail="Database connection failed")
    
    return _db_pool

async def get_redis():
    """Get or create Redis connection"""
    global _redis_client
    if _redis_client is None:
        try:
            import redis.asyncio as redis
            redis_url = os.environ.get('REDIS_URL', 'redis://redis:6379')
            _redis_client = redis.from_url(
                redis_url,
                max_connections=20,
                retry_on_timeout=True,
                socket_keepalive=True,
                health_check_interval=30
            )
            # Test connection
            await _redis_client.ping()
            logger.info("Redis connection established")
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}")
            _redis_client = None
    
    return _redis_client

# Database connection with pool reuse
async def get_db_connection():
    """Get database connection from pool"""
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

# JWT token functions
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=get_token_expire_minutes())
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, get_jwt_secret_key(), algorithm=get_jwt_algorithm())
    return encoded_jwt

def create_refresh_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=get_refresh_token_expire_days())
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, get_jwt_secret_key(), algorithm=get_jwt_algorithm())
    return encoded_jwt

def create_tokens(data: dict):
    """Create both access and refresh tokens and return a Token object"""
    from .schemas import Token
    
    access_token = create_access_token(data)
    refresh_token = create_refresh_token(data)
    expires_in = get_token_expire_minutes() * 60  # Convert to seconds
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=expires_in
    )

def verify_token(token: str):
    try:
        payload = jwt.decode(token, get_jwt_secret_key(), algorithms=[get_jwt_algorithm()])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return username
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def verify_refresh_token(token: str):
    try:
        payload = jwt.decode(token, get_jwt_secret_key(), algorithms=[get_jwt_algorithm()])
        username: str = payload.get("sub")
        token_type: str = payload.get("type")
        if username is None or token_type != "refresh":
            raise HTTPException(status_code=401, detail="Invalid refresh token")
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

async def get_current_user(token: str = Depends(oauth2_scheme)):
    # Check if token is revoked
    if token in revoked_tokens:
        raise HTTPException(status_code=401, detail="Token has been revoked")
    
    username = verify_token(token)
    return username

def revoke_token(token: str):
    """Add token to revoked tokens list"""
    revoked_tokens.add(token)

# Password utilities
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

# Health check function
async def health_check():
    """Comprehensive health check including Vault status"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "components": {}
    }
    
    # Check database connection
    try:
        async with asyncpg.create_pool(get_db_url(), min_size=1, max_size=1) as pool:
            async with pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
        health_status["components"]["database"] = {"status": "healthy"}
    except Exception as e:
        health_status["components"]["database"] = {"status": "unhealthy", "error": str(e)}
        health_status["status"] = "unhealthy"
    
    # Check Vault connection
    if VAULT_AVAILABLE:
        try:
            vault_health = vault_client.health_check()
            health_status["components"]["vault"] = vault_health
            if vault_health["status"] != "healthy":
                health_status["status"] = "degraded"
        except Exception as e:
            health_status["components"]["vault"] = {"status": "unhealthy", "error": str(e)}
            health_status["status"] = "degraded"
    else:
        health_status["components"]["vault"] = {"status": "unavailable", "note": "Using fallback configuration"}
        health_status["status"] = "degraded"
    
    # Check JWT configuration
    try:
        test_token = create_access_token({"sub": "health_check"})
        verify_token(test_token)
        health_status["components"]["jwt"] = {"status": "healthy"}
    except Exception as e:
        health_status["components"]["jwt"] = {"status": "unhealthy", "error": str(e)}
        health_status["status"] = "unhealthy"
    
    return health_status