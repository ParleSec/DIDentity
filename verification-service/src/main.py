from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from .schemas import CredentialVerify
from .dependencies import get_db_pool, logger
from prometheus_fastapi_instrumentator import Instrumentator
import json

app = FastAPI(
    title="DIDentity Verification Service",
    description="Credential verification and validation service for DIDentity platform",
    version="1.0.0",
    openapi_url=None,
    docs_url=None,
    redoc_url=None,
    openapi_tags=[
        {
            "name": "verification",
            "description": "Credential verification operations"
        },
        {
            "name": "health",
            "description": "Health check endpoint"
        }
    ]
)
Instrumentator().instrument(app).expose(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url="/openapi.json",
        title=app.title + " - Swagger UI",
        oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
        swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@3/swagger-ui-bundle.js",
        swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@3/swagger-ui.css",
    )

@app.get("/redoc", include_in_schema=False)
async def redoc_html():
    return get_redoc_html(
        openapi_url="/openapi.json",
        title=app.title + " - ReDoc",
        redoc_js_url="https://cdn.jsdelivr.net/npm/redoc@next/bundles/redoc.standalone.js",
    )

@app.get("/openapi.json", include_in_schema=False)
async def get_openapi_schema():
    openapi_schema = app.openapi()
    # Force OpenAPI 3.0.3 for Swagger UI compatibility
    openapi_schema["openapi"] = "3.0.3"
    return JSONResponse(content=openapi_schema)

@app.post("/credentials/verify", tags=["verification"])
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

@app.get("/health", tags=["health"])
async def health_check():
    try:
        pool = await get_db_pool().__anext__()
        async with pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {"status": "unhealthy", "error": str(e)}