"""
Unit tests for authentication endpoints.
"""
import pytest
from httpx import AsyncClient
from fastapi import status
from datetime import datetime
from unittest.mock import MagicMock

from app.main import app
from app.core.database import get_database
from app.models.user import UserRole


@pytest.mark.asyncio
async def test_register_user_success(client):
    """Test successful user registration."""
    user_data = {
        "name": "Test User",
        "email": "test@example.com",
        "password": "TestPassword123!",
        "role": "analyst"
    }
    
    response = await client.post("/api/v1/auth/register", json=user_data)
    
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    
    # Check response structure
    assert "access_token" in data
    assert "token_type" in data
    assert "expires_in" in data
    assert "user" in data
    
    # Check token type
    assert data["token_type"] == "bearer"
    assert data["expires_in"] == 1800  # 30 minutes
    
    # Check user data
    user = data["user"]
    assert user["name"] == "Test User"
    assert user["email"] == "test@example.com"
    assert user["role"] == "analyst"
    assert user["is_active"] is True


@pytest.mark.asyncio
async def test_register_user_duplicate_email(client):
    """Test registration with duplicate email."""
    user_data = {
        "name": "Test User",
        "email": "duplicate@example.com",
        "password": "TestPassword123!",
        "role": "analyst"
    }
    
    # First registration should succeed
    response1 = await client.post("/api/v1/auth/register", json=user_data)
    assert response1.status_code == status.HTTP_201_CREATED
    
    # Second registration with same email should fail
    response2 = await client.post("/api/v1/auth/register", json=user_data)
    assert response2.status_code == status.HTTP_400_BAD_REQUEST
    
    data = response2.json()
    assert "User with this email already exists" in data["message"]


@pytest.mark.asyncio
async def test_register_user_weak_password(client):
    """Test registration with weak password."""
    user_data = {
        "name": "Test User",
        "email": "weak@example.com",
        "password": "weak",  # Too weak
        "role": "analyst"
    }
    
    response = await client.post("/api/v1/auth/register", json=user_data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    data = response.json()
    assert "Validation error" in data["message"]


@pytest.mark.asyncio
async def test_login_success(client):
    """Test successful user login."""
    # First register a user
    user_data = {
        "name": "Login Test User",
        "email": "login@example.com",
        "password": "LoginPassword123!",
        "role": "admin"
    }
    
    register_response = await client.post("/api/v1/auth/register", json=user_data)
    assert register_response.status_code == status.HTTP_201_CREATED
    
    # Now test login
    login_data = {
        "email": "login@example.com",
        "password": "LoginPassword123!"
    }
    
    response = await client.post("/api/v1/auth/login", json=login_data)
    assert response.status_code == status.HTTP_200_OK
    
    data = response.json()
    
    # Check response structure
    assert "access_token" in data
    assert "token_type" in data
    assert "expires_in" in data
    assert "user" in data
    
    # Check user data
    user = data["user"]
    assert user["email"] == "login@example.com"
    assert user["role"] == "admin"


@pytest.mark.asyncio
async def test_login_invalid_credentials(client):
    """Test login with invalid credentials."""
    login_data = {
        "email": "nonexistent@example.com",
        "password": "WrongPassword123!"
    }
    
    response = await client.post("/api/v1/auth/login", json=login_data)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    data = response.json()
    assert "Incorrect email or password" in data["detail"]


@pytest.mark.asyncio
async def test_get_current_user(client):
    """Test getting current user information."""
    # Register and login to get token
    user_data = {
        "name": "Current User Test",
        "email": "current@example.com",
        "password": "CurrentPassword123!",
        "role": "analyst"
    }
    
    register_response = await client.post("/api/v1/auth/register", json=user_data)
    assert register_response.status_code == status.HTTP_201_CREATED
    
    token = register_response.json()["access_token"]
    
    # Test /me endpoint
    headers = {"Authorization": f"Bearer {token}"}
    response = await client.get("/api/v1/auth/me", headers=headers)
    
    assert response.status_code == status.HTTP_200_OK
    
    data = response.json()
    assert data["name"] == "Current User Test"
    assert data["email"] == "current@example.com"
    assert data["role"] == "analyst"


@pytest.mark.asyncio
async def test_get_current_user_invalid_token(client):
    """Test getting current user with invalid token."""
    headers = {"Authorization": "Bearer invalid_token"}
    response = await client.get("/api/v1/auth/me", headers=headers)
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
async def test_refresh_token(client):
    """Test token refresh functionality."""
    # Register and login to get token
    user_data = {
        "name": "Refresh Test User",
        "email": "refresh@example.com",
        "password": "RefreshPassword123!",
        "role": "analyst"
    }
    
    register_response = await client.post("/api/v1/auth/register", json=user_data)
    assert register_response.status_code == status.HTTP_201_CREATED
    
    token = register_response.json()["access_token"]
    
    # Test token refresh
    headers = {"Authorization": f"Bearer {token}"}
    response = await client.post("/api/v1/auth/refresh", headers=headers)
    
    assert response.status_code == status.HTTP_200_OK
    
    data = response.json()
    assert "access_token" in data
    assert "token_type" in data
    assert data["token_type"] == "bearer"
    
    # New token should be different from original
    assert data["access_token"] != token


@pytest.mark.asyncio
async def test_password_validation(client):
    """Test various password validation scenarios."""
    base_user_data = {
        "name": "Password Test User",
        "email": "password@example.com",
        "role": "analyst"
    }
    
    # Test cases for invalid passwords
    test_cases = [
        ("short", 422),  # Too short - caught by Pydantic validation
        ("nouppercase123!", 400),  # No uppercase - caught by our validation
        ("NOLOWERCASE123!", 400),  # No lowercase - caught by our validation
        ("NoDigits!", 400),  # No digits - caught by our validation
        ("NoSpecialChars123", 400),  # No special characters - caught by our validation
    ]
    
    for password, expected_status in test_cases:
        user_data = {**base_user_data, "password": password, "email": f"test_{password}@example.com"}
        response = await client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == expected_status
        
        data = response.json()
        if expected_status == 400:
            assert "Password does not meet security requirements" in data["message"]
        elif expected_status == 422:
            assert "Validation error" in data["message"]


@pytest.mark.asyncio
async def test_role_based_access(client):
    """Test role-based access control."""
    # Register admin user
    admin_data = {
        "name": "Admin User",
        "email": "admin@example.com",
        "password": "AdminPassword123!",
        "role": "admin"
    }
    
    admin_response = await client.post("/api/v1/auth/register", json=admin_data)
    assert admin_response.status_code == status.HTTP_201_CREATED
    
    admin_user = admin_response.json()["user"]
    assert admin_user["role"] == "admin"
    
    # Register analyst user
    analyst_data = {
        "name": "Analyst User",
        "email": "analyst@example.com",
        "password": "AnalystPassword123!",
        "role": "analyst"
    }
    
    analyst_response = await client.post("/api/v1/auth/register", json=analyst_data)
    assert analyst_response.status_code == status.HTTP_201_CREATED
    
    analyst_user = analyst_response.json()["user"]
    assert analyst_user["role"] == "analyst"