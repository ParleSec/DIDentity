from fastapi import FastAPI, Depends, HTTPException, status, BackgroundTasks, Request
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import logging
import os
import json
import asyncpg
from .schemas import UserCreate, UserLogin, Token, TokenRefresh, TokenRevoke
from .dependencies import get_db_pool, oauth2_scheme, verify_token, verify_refresh_token, pwd_context, logger, get_db_url, get_redis
from .dependencies import create_access_token, create_refresh_token, create_tokens, revoke_token
from .messaging import event_bus
# Temporarily disable telemetry due to import issues
# from .telemetry import extract_context_from_request, create_span, add_span_attributes, mark_span_error
from contextlib import nullcontext
extract_context_from_request = lambda x: None
create_span = lambda *args, **kwargs: nullcontext()
add_span_attributes = lambda x: None
mark_span_error = lambda x: None
from prometheus_fastapi_instrumentator import Instrumentator

# Set service name for messaging
os.environ["SERVICE_NAME"] = "auth-service"

# Setup logging
logger = logging.getLogger(__name__)

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting up auth service...")
    await event_bus.connect()
    logger.info("Auth service startup complete")
    
    yield
    
    # Shutdown
    logger.info("Shutting down auth service...")
    await event_bus.close()
    logger.info("Auth service shutdown complete")

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
    redoc_url=None,
    openapi_url=None,
    lifespan=lifespan
)

# Add rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add instrumentation
Instrumentator().instrument(app).expose(app)

# Add CORS middleware with more restrictive settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React development
        "http://localhost:8080",  # Vue development
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=[
        "Authorization",
        "Content-Type",
        "X-Requested-With",
        "Accept",
        "Origin",
        "X-CSRF-Token"
    ],
    expose_headers=["X-RateLimit-Limit", "X-RateLimit-Remaining"],
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
@limiter.limit("100/minute")  # Limit signup attempts to prevent abuse
async def signup(request: Request, user: UserCreate, background_tasks: BackgroundTasks, pool=Depends(get_db_pool)):
    """
    Register a new user and return an access token.
    
    - **username**: Required username (must be unique, 3-50 chars, alphanumeric + underscore/hyphen)
    - **email**: Required valid email address
    - **password**: Required strong password (min 12 chars, uppercase, lowercase, digit, special char)
    
    Rate limited to 100 attempts per minute per IP address.
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

                # Check if username exists
                existing_username = await conn.fetchrow(
                    "SELECT id FROM users WHERE username = $1", user.username
                )
                if existing_username:
                    logger.warning(f"Signup attempt with existing username: {user.username}")
                    raise HTTPException(
                        status_code=400,
                        detail="Username already taken"
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
@limiter.limit("500/minute")  # Limit login attempts to prevent brute force
async def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Authenticate a user and return an access token.
    
    Rate limited to 500 attempts per minute per IP address to prevent brute force attacks.
    """
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            # Find user
            user = await conn.fetchrow(
                "SELECT id, email, password_hash FROM users WHERE email = $1", 
                form_data.username  # OAuth2PasswordRequestForm uses username field for email
            )
            
            if not user or not pwd_context.verify(form_data.password, user["password_hash"]):
                # Log the failed attempt
                logger.warning(f"Failed login attempt for email: {form_data.username} from IP: {get_remote_address(request)}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Incorrect email or password",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            # Create tokens
            token_data = {"sub": user["email"], "user_id": str(user["id"])}
            tokens = create_tokens(token_data)
            
            logger.info(f"User logged in: {user['email']} from IP: {get_remote_address(request)}")
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
@limiter.limit("5/minute")  # Rate limit token endpoint
async def token(request: Request, form_data: OAuth2PasswordRequestForm = Depends(), pool=Depends(get_db_pool)):
    """
    OAuth2 compatible token endpoint.
    
    Rate limited to 5 attempts per minute per IP address.
    """
    # Reuse login logic
    return await login(request, form_data)

@app.post("/token/refresh", response_model=Token, tags=["auth"])
@limiter.limit("1000/minute")  # Rate limit token refresh
async def refresh_token(request: Request, token_data: TokenRefresh):
    """
    Refresh an access token using a refresh token.
    
    - **refresh_token**: Valid refresh token previously issued
    
    Returns a new access token and refresh token pair.
    Rate limited to 1000 attempts per minute per IP address.
    """
    try:
        # Verify refresh token
        payload = await verify_refresh_token(token_data.refresh_token)
        
        # Revoke old refresh token
        await revoke_token(token_data.refresh_token)
        
        # Create new tokens
        user_data = {"sub": payload["sub"], "user_id": payload["user_id"]}
        tokens = create_tokens(user_data)
        
        logger.info(f"Refreshed token for user: {payload['sub']} from IP: {get_remote_address(request)}")
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
@limiter.limit("1000/minute")  # Allow more revoke attempts
async def revoke_token_endpoint(request: Request, token_data: TokenRevoke, current_user: dict = Depends(verify_token)):
    """
    Revoke an access or refresh token.
    
    Rate limited to 1000 attempts per minute per IP address.
    """
    try:
        await revoke_token(token_data.token)
        logger.info(f"Token revoked for user: {current_user} from IP: {get_remote_address(request)}")
        return {"message": "Token revoked successfully"}
    except Exception as e:
        logger.error(f"Error revoking token: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to revoke token"
        )

@app.get("/health", tags=["health"])
@limiter.limit("3000/minute")  # Rate limit health checks
async def health_check(request: Request):
    """
    Health check endpoint that verifies the service and database connection.
    
    Rate limited to 3000 requests per minute per IP address.
    """
    try:
        # Use existing pool instead of creating new connection
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        
        # Test Redis if available
        redis_status = "not_configured"
        try:
            redis = await get_redis()
            if redis:
                await redis.ping()
                redis_status = "connected"
        except Exception:
            redis_status = "error"
            
        return {
            "status": "healthy", 
            "database": "connected",
            "redis": redis_status,
            "pool_stats": {
                "size": pool.get_size(),
                "idle": pool.get_idle_size()
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {"status": "unhealthy", "error": str(e)}

@app.get("/test", tags=["health"])
async def test():
    """
    Simple test endpoint to verify the service is running.
    """
    return {"message": "Auth service is running"}