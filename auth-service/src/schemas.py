from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
import re

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(
        ..., 
        min_length=12, 
        max_length=128,
        description="Password must be at least 12 characters with uppercase, lowercase, digit, and special character"
    )
    
    @validator('password')
    def validate_password_strength(cls, v):
        """Validate password strength requirements"""
        if len(v) < 12:
            raise ValueError('Password must be at least 12 characters long')
        
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Password must contain at least one special character (!@#$%^&*(),.?":{}|<>)')
        
        # Check for common weak patterns
        common_patterns = ['123456', 'password', 'qwerty', 'abc123', '111111']
        if any(pattern in v.lower() for pattern in common_patterns):
            raise ValueError('Password contains common weak patterns')
        
        return v
    
    @validator('username')
    def validate_username(cls, v):
        """Validate username format"""
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Username can only contain letters, numbers, underscores, and hyphens')
        return v

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    expires_in: int = 1800  # 30 minutes in seconds

class TokenRefresh(BaseModel):
    refresh_token: str

class TokenRevoke(BaseModel):
    token: str
    token_type_hint: Optional[str] = "access_token"  # or "refresh_token"