from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from .schemas import CredentialIssue
from .dependencies import get_db_pool, logger
from prometheus_fastapi_instrumentator import Instrumentator
import uuid
import json

app = FastAPI(
    title="DIDentity Credential Service",
    description="Verifiable credential issuance and management service for DIDentity platform",
    version="1.0.0",
    openapi_url=None,
    docs_url=None,
    redoc_url=None,
    openapi_tags=[
        {
            "name": "credentials",
            "description": "Credential issuance and management operations"
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

@app.post("/credentials/issue", tags=["credentials"])
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
                "INSERT INTO credentials (credential_id, issuer, holder, type, credential) VALUES ($1, 'system', $2, 'VerifiableCredential', $3)",
                credential_id, cred.holder_did, json.dumps(cred.credential_data)
            )
            
            logger.info(f"Successfully issued credential: {credential_id}")
            return {"credential_id": credential_id}
    except HTTPException as he:
        raise
    except Exception as e:
        logger.error(f"Failed to issue credential: {str(e)}")
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