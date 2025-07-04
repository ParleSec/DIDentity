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
import asyncio
import time
from dataclasses import dataclass

# Add vault directory to Python path
sys.path.append('/app/vault')

try:
    from vault_client import VaultClient, VaultClientError
    vault_client = VaultClient()
    VAULT_AVAILABLE = True
except ImportError:
    logging.warning("Vault client not available - THIS IS NOT SECURE FOR PRODUCTION")
    VAULT_AVAILABLE = False

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

@dataclass
class PoolMonitoringStats:
    """Database pool monitoring statistics"""
    total_requests: int = 0
    successful_connections: int = 0
    failed_connections: int = 0
    avg_connection_time: float = 0.0
    max_connection_time: float = 0.0
    last_health_check: Optional[datetime] = None
    pool_exhaustion_count: int = 0
    
# Global pool monitoring
_pool_stats = PoolMonitoringStats()

# Get secrets from Vault with fallback
def get_secret(path, key=None):
    """Get secret from Vault - NO FALLBACK FOR PRODUCTION SECURITY"""
    if VAULT_AVAILABLE:
        try:
            return vault_client.get_secret(path, key)
        except VaultClientError as e:
            logger.error(f"Error fetching secret from Vault: {e}")
            raise HTTPException(
                status_code=500,
                detail="Vault connection required for secure operation. Please check Vault configuration."
            )
    
    # SECURITY: NO FALLBACK FOR JWT SECRETS IN PRODUCTION
    if path == 'auth/jwt' and key == 'secret_key':
        raise HTTPException(
            status_code=500,
            detail="JWT secret key must be retrieved from Vault for security. Fallback secrets are not allowed."
        )
    
    # Limited fallback only for non-security-critical settings
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
        if key == 'algorithm':
            return os.environ.get('JWT_ALGORITHM', 'HS256')
        elif key == 'token_expire_minutes':
            return int(os.environ.get('JWT_EXPIRE_MINUTES', '30'))
        elif key == 'refresh_token_expire_days':
            return int(os.environ.get('JWT_REFRESH_EXPIRE_DAYS', '7'))
    
    raise HTTPException(
        status_code=500,
        detail=f"Failed to retrieve secret: {path}/{key} - Vault connection required"
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
    """Get JWT secret key from Vault - NO FALLBACK FOR SECURITY"""
    if VAULT_AVAILABLE:
        try:
            return vault_client.get_jwt_secret_key()
        except VaultClientError as e:
            logger.error(f"Failed to get JWT secret from Vault: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="JWT secret key must be retrieved from Vault for security"
            )
    
    # SECURITY: NO FALLBACK FOR JWT SECRETS
    raise HTTPException(
        status_code=500,
        detail="Vault connection required for JWT secret key. Production systems must not use fallback secrets."
    )

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

# Global connection pool (reuse across requests)
_db_pool = None
_redis_client = None

async def get_db_pool():
    """Get or create database connection pool with enhanced monitoring"""
    global _db_pool, _pool_stats
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
                max_inactive_connection_lifetime=300,  # 5 minutes
                # Enhanced monitoring callbacks
                setup=_setup_connection,
                init=_init_connection
            )
            logger.info(f"Database pool created: min=10, max=50")
            
            # Start pool monitoring task
            asyncio.create_task(_monitor_pool_health())
            
        except Exception as e:
            logger.error(f"Failed to create database pool: {e}")
            _pool_stats.failed_connections += 1
            raise HTTPException(status_code=500, detail="Database connection failed")
    
    return _db_pool

async def _setup_connection(conn):
    """Setup callback for new connections"""
    await conn.execute("SET timezone = 'UTC'")
    await conn.execute("SET statement_timeout = '30s'")

async def _init_connection(conn):
    """Initialize callback for each connection acquisition"""
    _pool_stats.successful_connections += 1

async def _monitor_pool_health():
    """Background task to monitor pool health"""
    global _db_pool, _pool_stats
    
    while True:
        try:
            await asyncio.sleep(60)  # Check every minute
            
            if _db_pool is None:
                continue
            
            # Log pool statistics
            pool_size = _db_pool.get_size()
            idle_size = _db_pool.get_idle_size()
            used_connections = pool_size - idle_size
            
            # Check for pool exhaustion
            if idle_size == 0 and pool_size >= 45:  # 90% of max pool size
                _pool_stats.pool_exhaustion_count += 1
                logger.warning(f"Database pool near exhaustion: {used_connections}/{pool_size} connections in use")
            
            # Log health metrics every 5 minutes
            now = datetime.now(timezone.utc)
            if (_pool_stats.last_health_check is None or 
                (now - _pool_stats.last_health_check).total_seconds() >= 300):
                
                _pool_stats.last_health_check = now
                logger.info(f"Pool Health - Size: {pool_size}, Idle: {idle_size}, "
                          f"Success Rate: {_pool_stats.successful_connections}/{_pool_stats.total_requests}, "
                          f"Exhaustion Events: {_pool_stats.pool_exhaustion_count}")
                
                # Alert if pool performance is poor
                if _pool_stats.total_requests > 0:
                    success_rate = _pool_stats.successful_connections / _pool_stats.total_requests
                    if success_rate < 0.95:  # Less than 95% success rate
                        logger.warning(f"Poor database pool performance: {success_rate:.2%} success rate")
                        
        except Exception as e:
            logger.error(f"Pool monitoring error: {e}")

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

# Database connection with pool reuse and monitoring
async def get_db_connection():
    """Get database connection from pool with monitoring"""
    global _pool_stats
    start_time = time.time()
    _pool_stats.total_requests += 1
    
    try:
        pool = await get_db_pool()
        if not pool:
            _pool_stats.failed_connections += 1
            raise HTTPException(status_code=500, detail="Database pool not available")
        
        # Monitor connection acquisition time
        async with pool.acquire() as conn:
            connection_time = time.time() - start_time
            
            # Update timing statistics
            if connection_time > _pool_stats.max_connection_time:
                _pool_stats.max_connection_time = connection_time
                
            # Update running average
            if _pool_stats.avg_connection_time == 0:
                _pool_stats.avg_connection_time = connection_time
            else:
                _pool_stats.avg_connection_time = (
                    _pool_stats.avg_connection_time * 0.9 + connection_time * 0.1
                )
            
            # Alert on slow connections
            if connection_time > 5.0:  # More than 5 seconds
                logger.warning(f"Slow database connection acquisition: {connection_time:.2f}s")
            
            yield conn
            
    except asyncpg.InvalidPasswordError:
        _pool_stats.failed_connections += 1
        logger.error("Database authentication failed")
        raise HTTPException(status_code=500, detail="Database authentication failed")
    except asyncpg.TooManyConnectionsError:
        _pool_stats.failed_connections += 1
        _pool_stats.pool_exhaustion_count += 1
        logger.error("Database pool exhausted - too many connections")
        raise HTTPException(status_code=503, detail="Service temporarily unavailable - high load")
    except Exception as e:
        _pool_stats.failed_connections += 1
        logger.error(f"Database connection error: {str(e)}")
        raise HTTPException(status_code=500, detail="Database connection error")

def get_pool_stats():
    """Get current pool monitoring statistics"""
    return _pool_stats

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
    """Get current user and check if token is revoked using Redis"""
    # Check if token is revoked using Redis
    redis_client = await get_redis()
    if redis_client:
        try:
            is_revoked = await redis_client.get(f"revoked_token:{token}")
            if is_revoked:
                raise HTTPException(status_code=401, detail="Token has been revoked")
        except Exception as e:
            logger.warning(f"Redis token check failed: {e}")
            # Continue without Redis check if Redis is unavailable
    
    username = verify_token(token)
    return username

async def revoke_token(token: str):
    """Add token to revoked tokens list using Redis"""
    redis_client = await get_redis()
    if redis_client:
        try:
            # Store revoked token with expiration matching token expiration
            expire_minutes = get_token_expire_minutes()
            await redis_client.setex(
                f"revoked_token:{token}", 
                expire_minutes * 60,  # Convert to seconds
                "revoked"
            )
            logger.info("Token revoked and stored in Redis")
        except Exception as e:
            logger.error(f"Failed to revoke token in Redis: {e}")
            raise HTTPException(
                status_code=500, 
                detail="Failed to revoke token securely"
            )
    else:
        logger.error("Redis not available for secure token revocation")
        raise HTTPException(
            status_code=500,
            detail="Secure token revocation requires Redis connection"
        )

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