from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from .schemas import UserCreate, UserLogin, Token
from .dependencies import get_db_pool, oauth2_scheme, verify_token, pwd_context, logger, create_access_token
from prometheus_fastapi_instrumentator import Instrumentator

# Initialize instrumentation before creating any routes
app = FastAPI()
Instrumentator().instrument(app).expose(app)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/signup", response_model=Token)
async def signup(user: UserCreate, pool=Depends(get_db_pool)):
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
            
            # Create token
            token_data = {"sub": user.email, "user_id": str(user_id)}
            access_token = create_access_token(token_data)
            
            logger.info(f"Successfully created user with email: {user.email}")
            return {"access_token": access_token, "token_type": "bearer"}

    except HTTPException as he:
        logger.error(f"HTTP Exception during signup: {str(he)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during signup: {str(e)}")
        logger.exception(e)
        raise HTTPException(
            status_code=500,
            detail="Internal server error during user registration"
        )

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

@app.get("/test")
async def test():
    return {"message": "Auth service is running"}