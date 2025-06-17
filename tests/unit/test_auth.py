import pytest
from auth_service.src.dependencies import create_access_token, verify_token
from auth_service.src.schemas import UserCreate
from fastapi import HTTPException
from pydantic import ValidationError

def test_user_create_schema():
    # Valid user data
    valid_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "SecurePass123"
    }
    user = UserCreate(**valid_data)
    assert user.username == valid_data["username"]
    assert user.email == valid_data["email"]
    assert user.password == valid_data["password"]

    # Invalid email
    with pytest.raises(ValidationError):
        UserCreate(username="test", email="invalid-email", password="pass123")

    # Short password
    with pytest.raises(ValidationError):
        UserCreate(username="test", email="test@example.com", password="short")

def test_token_creation_and_verification():
    data = {"sub": "test@example.com", "user_id": "1"}
    token = create_access_token(data)
    
    # Verify token
    username = verify_token(token)
    assert username == data["sub"]

    # Invalid token
    with pytest.raises(HTTPException):
        verify_token("invalid.token.here")
