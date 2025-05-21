from fastapi import FastAPI, Depends, HTTPException, status, BackgroundTasks, Request
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from .schemas import UserCreate, UserLogin, Token, TokenRefresh, TokenRevoke
from .dependencies import get_db_pool, oauth2_scheme, verify_token, verify_refresh_token, pwd_context, logger
from .dependencies import create_access_token, create_refresh_token, create_tokens, revoke_token
from .messaging import event_bus
from .telemetry import extract_context_from_request, create_span, add_span_attributes, mark_span_error
from prometheus_fastapi_instrumentator import Instrumentator
import os
import json

# Set service name for messaging
os.environ["SERVICE_NAME"] = "auth-service"

# Initialize FastAPI with enhanced metadata
app = FastAPI(
    title="DIDentity Auth Service",
    description="Authentication and authorization service for DIDentity platform",
    version="1.0.0",
    openapi_tags=[
        {
            "name": "auth",
            "description": "Authentication and user management operations"
        },
        {
            "name": "health",
            "description": "Health check endpoint"
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

@app.post("/signup", response_model=Token, tags=["auth"])
async def signup(user: UserCreate, background_tasks: BackgroundTasks, request: Request, pool=Depends(get_db_pool)):
    """
    Register a new user and return an access token.
    
    - **username**: Required username (must be unique)
    - **email**: Required valid email address
    - **password**: Required password (min length: 8)
    """
    # Create a tracing span
    context = extract_context_from_request(request)
    with create_span("signup", context=context, attributes={"email": user.email}) as span:
        logger.info(f"Processing signup request for email: {user.email}")
        try:
            async with pool.acquire() as conn:
                # Check if user exists
                existing_user = await conn.fetchrow(
                    "SELECT id FROM users WHERE email = $1", user.email
                )
                if existing_user:
                    logger.warning(f"Signup attempt with existing email: {user.email}")
                    raise HTTPException(
                        status_code=400,
                        detail="Email already registered"
                    )

                # Create user
                hashed_password = pwd_context.hash(user.password)
                query = """
                    INSERT INTO users (username, email, password_hash) 
                    VALUES ($1, $2, $3) 
                    RETURNING id
                """
                user_id = await conn.fetchval(query, user.username, user.email, hashed_password)
                
                # Create tokens
                token_data = {"sub": user.email, "user_id": str(user_id)}
                tokens = create_tokens(token_data)
                
                # Add span attributes
                add_span_attributes({"user_id": str(user_id)})
                
                # Publish user created event asynchronously
                background_tasks.add_task(
                    event_bus.publish,
                    "user.created",
                    {"user_id": str(user_id), "email": user.email, "username": user.username}
                )
                
                logger.info(f"Successfully created user with email: {user.email}")
                return tokens

        except HTTPException as he:
            logger.error(f"HTTP Exception during signup: {str(he)}")
            mark_span_error(he)
            raise
        except Exception as e:
            logger.error(f"Unexpected error during signup: {str(e)}")
            logger.exception(e)
            mark_span_error(e)
            raise HTTPException(
                status_code=500,
                detail="Internal server error during user registration"
            )

@app.post("/login", response_model=Token, tags=["auth"])
async def login(form_data: OAuth2PasswordRequestForm = Depends(), pool=Depends(get_db_pool)):
    """
    Authenticate a user and return an access token.
    """
    try:
        async with pool.acquire() as conn:
            # Find user
            user = await conn.fetchrow(
                "SELECT id, email, password_hash FROM users WHERE email = $1", 
                form_data.username  # OAuth2PasswordRequestForm uses username field for email
            )
            
            if not user or not pwd_context.verify(form_data.password, user["password_hash"]):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Incorrect email or password",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            # Create tokens
            token_data = {"sub": user["email"], "user_id": str(user["id"])}
            tokens = create_tokens(token_data)
            
            logger.info(f"User logged in: {user['email']}")
            return tokens
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during login: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error during login"
        )

@app.post("/token", response_model=Token, tags=["auth"])
async def token(form_data: OAuth2PasswordRequestForm = Depends(), pool=Depends(get_db_pool)):
    """
    OAuth2 compatible token endpoint.
    
    This endpoint is used for obtaining access tokens through the Password Grant flow.
    It is compatible with standard OAuth2 clients.
    """
    # Reuse the login endpoint implementation
    return await login(form_data, pool)

@app.post("/token/refresh", response_model=Token, tags=["auth"])
async def refresh_token(token_data: TokenRefresh):
    """
    Refresh an access token using a refresh token.
    
    - **refresh_token**: Valid refresh token previously issued
    
    Returns a new access token and refresh token pair.
    """
    try:
        # Verify refresh token
        payload = await verify_refresh_token(token_data.refresh_token)
        
        # Revoke old refresh token
        revoke_token(token_data.refresh_token)
        
        # Create new tokens
        user_data = {"sub": payload["sub"], "user_id": payload["user_id"]}
        tokens = create_tokens(user_data)
        
        logger.info(f"Refreshed token for user: {payload['sub']}")
        return tokens
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error refreshing token: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error during token refresh"
        )

@app.post("/token/revoke", tags=["auth"])
async def revoke_token_endpoint(token_data: TokenRevoke, current_user: dict = Depends(verify_token)):
    """
    Revoke a token so it can no longer be used.
    
    - **token**: The token to revoke
    - **token_type_hint**: Type of token ("access_token" or "refresh_token")
    
    Requires authentication with a valid access token.
    """
    try:
        # Add token to revocation list
        revoke_token(token_data.token)
        return {"message": "Token revoked successfully"}
    except Exception as e:
        logger.error(f"Error revoking token: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error during token revocation"
        )

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

@app.get("/test", tags=["health"])
async def test():
    """
    Simple test endpoint to verify the service is running.
    """
    return {"message": "Auth service is running"}