from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from .schemas import DIDCreate, DIDDocument
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

@app.post("/dids", response_model=DIDDocument)
async def create_did(did: DIDCreate, pool=Depends(get_db_pool)):
    logger.info(f"Creating DID with method: {did.method}")
    try:
        async with pool.acquire() as conn:
            did_id = f"did:{did.method}:{did.identifier}"
            
            # Check if DID exists
            existing_did = await conn.fetchrow(
                "SELECT id FROM dids WHERE did = $1", did_id
            )
            if existing_did:
                logger.warning(f"Attempt to create existing DID: {did_id}")
                raise HTTPException(status_code=400, detail="DID already exists")

            # Create DID document
            did_document = {
                "id": did_id,
                "public_key": f"{did_id}#key-1",
                "authentication": [f"{did_id}#key-1"]
            }

            # Store DID - convert document to JSON string
            await conn.execute(
                "INSERT INTO dids (did, document) VALUES ($1, $2)",
                did_id, json.dumps(did_document)
            )
            
            logger.info(f"Successfully created DID: {did_id}")
            return did_document
    except HTTPException as he:
        raise
    except Exception as e:
        logger.error(f"Error creating DID: {str(e)}")
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