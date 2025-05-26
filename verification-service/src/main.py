from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from .schemas import CredentialVerify
from .dependencies import get_db_pool, logger
from prometheus_fastapi_instrumentator import Instrumentator
import json

app = FastAPI()
Instrumentator().instrument(app).expose(app)

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
                JOIN dids d ON c.holder = d.did 
                WHERE c.credential_id = $1
                """,
                cred.credential_id
            )
            
            if not credential:
                raise HTTPException(status_code=404, detail="Credential not found")

            # Parse JSON data
            credential_data = json.loads(credential['credential'])
            did_document = json.loads(credential['document'])

            verification_result = {
                "status": "valid",
                "credential_data": credential_data,
                "holder_did": credential["did"],
                "did_document": did_document
            }
            
            logger.info(f"Successfully verified credential: {cred.credential_id}")
            return verification_result
    except HTTPException as he:
        raise
    except Exception as e:
        logger.error(f"Failed to verify credential: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

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