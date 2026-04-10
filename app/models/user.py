"""
User-related Pydantic models.
"""
from datetime import datetime
from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, EmailStr, Field


class UserRole(str, Enum):
    """User roles for role-based access control."""
    ADMIN = "admin"
    ANALYST = "analyst"


class UserBase(BaseModel):
    """Base user model with common fields."""
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    role: UserRole = UserRole.ANALYST


class UserCreate(UserBase):
    """User creation model."""
    password: str = Field(..., min_length=8, max_length=128)


class UserLogin(BaseModel):
    """User login model."""
    email: EmailStr
    password: str


class UserResponse(UserBase):
    """User response model (excludes password)."""
    id: str = Field(alias="_id")
    created_at: datetime
    last_login: Optional[datetime] = None
    is_active: bool = True
    
    class Config:
        populate_by_name = True


class User(UserBase):
    """Complete user model for database storage."""
    id: Optional[Any] = Field(default=None, alias="_id")
    password_hash: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None
    is_active: bool = True
    failed_login_attempts: int = 0
    locked_until: Optional[datetime] = None
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True


class TokenResponse(BaseModel):
    """JWT token response model."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse