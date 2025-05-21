import asyncpg
import logging
from fastapi import HTTPException
from typing import AsyncGenerator

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Hardcoded connection string to ensure we're using the right format
DATABASE_URL = "postgresql://postgres:password@db:5432/decentralized_id"

async def get_db_pool() -> AsyncGenerator[asyncpg.Pool, None]:
    try:
        pool = await asyncpg.create_pool(
            DATABASE_URL,
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

# verification-service/src/main.py
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from .schemas import CredentialVerify
from .dependencies import get_db_pool, logger

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/credentials/verify")
async def verify_credential(cred: CredentialVerify, pool=Depends(get_db_pool)):
    logger.info(f"Verifying credential: {cred.credential_id}")
    try:
        async with pool.acquire() as conn:
            # Get credential data
            credential = await conn.fetchrow(
                """
                SELECT c.*, d.did, d.document 
                FROM credentials c 
                JOIN dids d ON c.holder_did = d.did 
                WHERE c.credential_id = $1
                """,
                cred.credential_id
            )
            
            if not credential:
                raise HTTPException(status_code=404, detail="Credential not found")

            # In a real system, we would do more verification here
            verification_result = {
                "status": "valid",
                "credential_data": credential["data"],
                "holder_did": credential["did"],
                "verification_time": "2024-02-24T00:00:00Z"
            }
            
            logger.info(f"Successfully verified credential: {cred.credential_id}")
            return verification_result
    except HTTPException as he:
        raise
    except Exception as e:
        logger.error(f"Failed to verify credential: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to verify credential")

@app.get("/health")
async def health_check():
    try:
        pool = await get_db_pool().__anext__()
        async with pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {"status": "unhealthy", "error": str(e)}