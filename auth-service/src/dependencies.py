import asyncpg
import logging
import hvac
import os
import uuid
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import JWTError, jwt
from typing import Optional, Dict, List
from fastapi import Depends, HTTPException, status

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
        # Fallback for local development
        if path == 'database/config' and key == 'url':
            return "postgresql://postgres:password@db:5432/decentralized_id"
        elif path == 'auth/jwt' and key == 'secret_key':
            return "your-very-secure-secret-key-here"
        elif path == 'auth/jwt' and key == 'algorithm':
            return "HS256"
        elif path == 'auth/jwt' and key == 'token_expire_minutes':
            return 30
        elif path == 'auth/jwt' and key == 'refresh_token_expire_days':
            return 7
        raise

# Constants from Vault
def get_db_url():
    return get_secret('database/config', 'url')

def get_jwt_settings():
    return {
        'secret_key': get_secret('auth/jwt', 'secret_key'),
        'algorithm': get_secret('auth/jwt', 'algorithm'),
        'expire_minutes': int(get_secret('auth/jwt', 'token_expire_minutes')),
        'refresh_expire_days': int(get_secret('auth/jwt', 'refresh_token_expire_days') or 7)
    }

# Security
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# In-memory blacklist for revoked tokens (in production, use Redis or a database)
# This is a simple implementation - for production, use a persistent store
revoked_tokens = set()

# Database connection
async def get_db_pool():
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

def create_access_token(data: Dict) -> str:
    """Create a new access token"""
    jwt_settings = get_jwt_settings()
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=jwt_settings['expire_minutes'])
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, jwt_settings['secret_key'], algorithm=jwt_settings['algorithm'])
    return encoded_jwt

def create_refresh_token(data: Dict) -> str:
    """Create a new refresh token"""
    jwt_settings = get_jwt_settings()
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=jwt_settings['refresh_expire_days'])
    jti = str(uuid.uuid4())  # Token identifier for revocation
    to_encode.update({"exp": expire, "type": "refresh", "jti": jti})
    encoded_jwt = jwt.encode(to_encode, jwt_settings['secret_key'], algorithm=jwt_settings['algorithm'])
    return encoded_jwt

def create_tokens(data: Dict) -> Dict:
    """Create both access and refresh tokens"""
    access_token = create_access_token(data)
    refresh_token = create_refresh_token(data)
    jwt_settings = get_jwt_settings()
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": jwt_settings['expire_minutes'] * 60  # in seconds
    }

async def verify_token(token: str = Depends(oauth2_scheme)) -> Dict:
    """Verify an access token"""
    jwt_settings = get_jwt_settings()
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Check if token is in blacklist
        if token in revoked_tokens:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been revoked",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        # Decode token
        payload = jwt.decode(token, jwt_settings['secret_key'], algorithms=[jwt_settings['algorithm']])
        
        # Check token type
        if payload.get("type") != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        return payload
    except JWTError:
        raise credentials_exception

async def verify_refresh_token(token: str) -> Dict:
    """Verify a refresh token"""
    jwt_settings = get_jwt_settings()
    
    try:
        # Check if token is in blacklist
        if token in revoked_tokens:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been revoked",
            )
            
        # Decode token
        payload = jwt.decode(token, jwt_settings['secret_key'], algorithms=[jwt_settings['algorithm']])
        
        # Check token type
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
            )
            
        return payload
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid refresh token: {str(e)}",
        )

def revoke_token(token: str):
    """Add a token to the revocation blacklist"""
    revoked_tokens.add(token)
    logger.info(f"Token revoked. Blacklist size: {len(revoked_tokens)}")
    return {"message": "Token revoked successfully"}