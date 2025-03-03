import asyncpg
import logging
from fastapi import HTTPException
from typing import AsyncGenerator

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

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

# credential-service/src/main.py
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from .schemas import CredentialIssue
from .dependencies import get_db_pool, logger
import uuid

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/credentials/issue")
async def issue_credential(cred: CredentialIssue, pool=Depends(get_db_pool)):
    logger.info(f"Issuing credential for DID: {cred.holder_did}")
    try:
        async with pool.acquire() as conn:
            # Verify DID exists
            did_exists = await conn.fetchval(
                "SELECT EXISTS(SELECT 1 FROM dids WHERE did = $1)",
                cred.holder_did
            )
            if not did_exists:
                raise HTTPException(status_code=404, detail="DID not found")

            credential_id = f"cred:{uuid.uuid4()}"
            await conn.execute(
                "INSERT INTO credentials (credential_id, holder_did, data) VALUES ($1, $2, $3)",
                credential_id, cred.holder_did, cred.credential_data
            )
            
            logger.info(f"Successfully issued credential: {credential_id}")
            return {"credential_id": credential_id}
    except HTTPException as he:
        raise
    except Exception as e:
        logger.error(f"Failed to issue credential: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to issue credential")

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
