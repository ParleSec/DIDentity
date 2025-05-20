from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from fastapi.responses import JSONResponse
from .schemas import DIDCreate, DIDDocument, VerificationMethod, DIDMethod, DIDResolution, DIDResolutionMetadata, DIDDocumentMetadata
from .dependencies import get_db_pool, logger
from .messaging import event_bus
from .telemetry import extract_context_from_request, create_span, add_span_attributes, mark_span_error
from prometheus_fastapi_instrumentator import Instrumentator
import json
import os
import uuid
from datetime import datetime

# Set service name for messaging
os.environ["SERVICE_NAME"] = "did-service"

# Initialize FastAPI with enhanced metadata
app = FastAPI(
    title="DIDentity DID Service",
    description="Decentralized Identifier (DID) management service for DIDentity platform",
    version="1.0.0",
    openapi_tags=[
        {
            "name": "dids",
            "description": "DID creation and management operations"
        },
        {
            "name": "health",
            "description": "Health check endpoint"
        },
        {
            "name": "sdk",
            "description": "SDK generation endpoints"
        }
    ],
    docs_url=None,
    redoc_url=None
)

# Add instrumentation
Instrumentator().instrument(app).expose(app)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    # Connect to RabbitMQ
    await event_bus.connect()
    
    # Subscribe to user.created events
    await event_bus.subscribe("user.created", handle_user_created)

@app.on_event("shutdown")
async def shutdown_event():
    # Close RabbitMQ connection
    await event_bus.close()

# Custom OpenAPI endpoints with SDK download options
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=app.title + " - Swagger UI",
        oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
        swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@3/swagger-ui-bundle.js",
        swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@3/swagger-ui.css",
    )

@app.get("/redoc", include_in_schema=False)
async def redoc_html():
    return get_redoc_html(
        openapi_url=app.openapi_url,
        title=app.title + " - ReDoc",
        redoc_js_url="https://cdn.jsdelivr.net/npm/redoc@next/bundles/redoc.standalone.js",
    )

# Export OpenAPI schema
@app.get("/openapi.json", include_in_schema=False)
async def get_openapi_schema():
    return JSONResponse(content=app.openapi())

# Endpoint to generate client SDKs
@app.get("/sdk/{language}", tags=["sdk"])
async def generate_sdk(language: str):
    """
    Generate client SDK for the specified language.
    Currently supported: 'typescript', 'python', 'java'
    """
    if language not in ["typescript", "python", "java"]:
        raise HTTPException(status_code=400, detail=f"SDK for {language} not available")
    
    # In a real implementation, you would generate the SDK here or return pre-generated SDKs
    return {
        "message": f"SDK for {language} would be generated here",
        "steps": [
            "1. Download the OpenAPI spec from /openapi.json",
            f"2. Use an OpenAPI generator tool to create a {language} client",
            "3. Example command: openapi-generator-cli generate -i openapi.json -g " + 
            language + " -o ./generated-client"
        ]
    }

def generate_did_document(did: str, method: DIDMethod, controller: str = None):
    """Generate a DID document based on method and parameters"""
    now = datetime.utcnow().isoformat() + "Z"
    controller = controller or did
    
    # Create different verification methods based on DID method
    if method == DIDMethod.KEY:
        key_id = f"{did}#keys-1"
        verification_method = VerificationMethod(
            id=key_id,
            type="Ed25519VerificationKey2020",
            controller=did,
            publicKeyMultibase="z" + did.split(":")[-1]  # Example format, would vary based on actual implementation
        )
    elif method == DIDMethod.WEB:
        key_id = f"{did}#keys-1"
        verification_method = VerificationMethod(
            id=key_id,
            type="Ed25519VerificationKey2020",
            controller=did,
            publicKeyJwk={
                "kty": "OKP",
                "crv": "Ed25519",
                "x": str(uuid.uuid4())  # Placeholder for actual key
            }
        )
    elif method == DIDMethod.ETHR:
        key_id = f"{did}#keys-1"
        addr = did.split(":")[-1]
        verification_method = VerificationMethod(
            id=key_id,
            type="EcdsaSecp256k1RecoveryMethod2020",
            controller=did,
            blockchainAccountId=f"eip155:1:{addr}"
        )
    else:
        # Default key type
        key_id = f"{did}#keys-1"
        verification_method = VerificationMethod(
            id=key_id,
            type="Ed25519VerificationKey2020",
            controller=did,
            publicKeyJwk={
                "kty": "OKP",
                "crv": "Ed25519",
                "x": str(uuid.uuid4())  # Placeholder for actual key
            }
        )
    
    # Create DID document
    did_document = DIDDocument(
        id=did,
        controller=controller,
        verificationMethod=[verification_method],
        authentication=[key_id]
    )
    
    # Resolution metadata
    resolution_metadata = DIDResolutionMetadata(
        contentType="application/did+json",
        retrieved=now
    )
    
    # Document metadata
    document_metadata = DIDDocumentMetadata(
        created=now,
        updated=now
    )
    
    # Full resolution object
    resolution = DIDResolution(
        didResolutionMetadata=resolution_metadata,
        didDocument=did_document,
        didDocumentMetadata=document_metadata
    )
    
    return resolution

async def handle_user_created(data):
    """Handle user.created events to automatically create a DID."""
    logger.info(f"Handling user.created event for user {data['user_id']}")
    try:
        # Create a DID for the new user
        user_id = data["user_id"]
        method = DIDMethod.ETHR  # Default method
        
        # Generate DID
        did_id = f"did:{method}:{user_id}"
        
        # Generate DID document
        resolution = generate_did_document(did_id, method)
        
        # Store in database
        pool = await get_db_pool().__anext__()
        async with pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO dids (did, document, user_id) VALUES ($1, $2, $3)",
                did_id, json.dumps(resolution.didDocument.dict(by_alias=True)), user_id
            )
        
        logger.info(f"Created DID {did_id} for user {user_id}")
        
        # Publish DID created event
        await event_bus.publish("did.created", {
            "did": did_id,
            "user_id": user_id
        })
    except Exception as e:
        logger.error(f"Error creating DID for user {data['user_id']}: {str(e)}")

@app.post("/dids", response_model=DIDDocument, tags=["dids"])
async def create_did(did: DIDCreate, background_tasks: BackgroundTasks, request: Request, pool=Depends(get_db_pool)):
    """
    Create a new Decentralized Identifier (DID)
    
    - **method**: DID method (e.g., 'ethr', 'web', 'key')
    - **identifier**: Unique identifier for the DID
    - **controller**: Optional controller of the DID
    
    Returns a DID document conforming to the W3C DID spec.
    """
    # Create a tracing span
    context = extract_context_from_request(request)
    with create_span("create_did", context=context, attributes={"method": did.method, "identifier": did.identifier}) as span:
        logger.info(f"Creating DID with method: {did.method}")
        try:
            # Generate DID
            did_id = f"did:{did.method}:{did.identifier}"
            
            async with pool.acquire() as conn:
                # Check if DID exists
                existing_did = await conn.fetchrow(
                    "SELECT id FROM dids WHERE did = $1", did_id
                )
                if existing_did:
                    logger.warning(f"Attempt to create existing DID: {did_id}")
                    raise HTTPException(status_code=400, detail="DID already exists")

                # Generate DID document
                resolution = generate_did_document(did_id, did.method, did.controller)
                did_document = resolution.didDocument
                
                # Store DID in database
                await conn.execute(
                    "INSERT INTO dids (did, document) VALUES ($1, $2)",
                    did_id, json.dumps(did_document.dict(by_alias=True))
                )
                
                # Add span attributes
                add_span_attributes({"did_id": did_id})
                
                # Publish DID created event asynchronously
                background_tasks.add_task(
                    event_bus.publish,
                    "did.created",
                    {"did": did_id}
                )
                
                logger.info(f"Successfully created DID: {did_id}")
                return did_document
        except HTTPException as he:
            mark_span_error(he)
            raise
        except Exception as e:
            logger.error(f"Error creating DID: {str(e)}")
            mark_span_error(e)
            raise HTTPException(status_code=500, detail=str(e))

@app.get("/dids/{did}", response_model=DIDResolution, tags=["dids"])
async def resolve_did(did: str, request: Request, pool=Depends(get_db_pool)):
    """
    Resolve a DID to its DID document
    
    - **did**: The full DID to resolve (e.g., 'did:ethr:0x1234...')
    
    Returns a DID Resolution object conforming to the W3C DID spec.
    """
    # Create a tracing span
    context = extract_context_from_request(request)
    with create_span("resolve_did", context=context, attributes={"did": did}) as span:
        logger.info(f"Resolving DID: {did}")
        try:
            async with pool.acquire() as conn:
                # Find DID in database
                result = await conn.fetchrow(
                    "SELECT document, created_at, updated_at FROM dids WHERE did = $1", did
                )
                
                if not result:
                    logger.warning(f"DID not found: {did}")
                    error_msg = "DID not found"
                    
                    resolution_metadata = DIDResolutionMetadata(
                        contentType="application/did+json",
                        retrieved=datetime.utcnow().isoformat() + "Z",
                        error=error_msg
                    )
                    
                    return DIDResolution(
                        didResolutionMetadata=resolution_metadata,
                        didDocument=DIDDocument(id=did),
                        didDocumentMetadata=DIDDocumentMetadata()
                    )
                
                # Parse document from database
                document = json.loads(result["document"])
                
                # Convert to DID document
                did_document = DIDDocument(**document)
                
                # Create resolution metadata
                resolution_metadata = DIDResolutionMetadata(
                    contentType="application/did+json",
                    retrieved=datetime.utcnow().isoformat() + "Z"
                )
                
                # Create document metadata
                document_metadata = DIDDocumentMetadata(
                    created=result["created_at"].isoformat() + "Z" if result["created_at"] else None,
                    updated=result["updated_at"].isoformat() + "Z" if result["updated_at"] else None
                )
                
                # Add span attributes
                add_span_attributes({"found": True})
                
                # Return full resolution
                return DIDResolution(
                    didResolutionMetadata=resolution_metadata,
                    didDocument=did_document,
                    didDocumentMetadata=document_metadata
                )
                
        except Exception as e:
            logger.error(f"Error resolving DID: {str(e)}")
            mark_span_error(e)
            raise HTTPException(status_code=500, detail=f"Error resolving DID: {str(e)}")

@app.get("/health", tags=["health"])
async def health_check():
    """
    Health check endpoint that verifies the service and database connection.
    """
    try:
        pool = await get_db_pool().__anext__()
        async with pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {"status": "unhealthy", "error": str(e)}