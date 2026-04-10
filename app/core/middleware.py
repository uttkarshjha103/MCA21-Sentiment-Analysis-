"""
Authentication and security middleware for the MCA21 system.
"""
import logging
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from .security import verify_token
from .database import get_database
from .exceptions import authentication_exception, authorization_exception
from ..models.user import User, UserRole

logger = logging.getLogger(__name__)

# HTTP Bearer token scheme
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db = Depends(get_database)
) -> User:
    """
    Get the current authenticated user from JWT token.
    """
    token = credentials.credentials
    payload = verify_token(token)
    
    if payload is None:
        logger.warning(f"Invalid token provided")
        raise authentication_exception("Invalid authentication token")
    
    user_id = payload.get("sub")
    if user_id is None:
        logger.warning("Token missing user ID")
        raise authentication_exception("Invalid token payload")
    
    # Get user from database
    user_doc = await db.users.find_one({"_id": user_id})
    if user_doc is None:
        logger.warning(f"User not found: {user_id}")
        raise authentication_exception("User not found")
    
    user = User(**user_doc)
    
    if not user.is_active:
        logger.warning(f"Inactive user attempted access: {user_id}")
        raise authentication_exception("User account is inactive")
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get the current active user (alias for get_current_user).
    """
    return current_user


def require_role(required_role: UserRole):
    """
    Dependency factory for role-based access control.
    """
    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role != required_role and current_user.role != UserRole.ADMIN:
            logger.warning(
                f"User {current_user.id} with role {current_user.role} "
                f"attempted to access {required_role} endpoint"
            )
            raise authorization_exception(
                f"Access denied. Required role: {required_role.value}"
            )
        return current_user
    
    return role_checker


def require_admin():
    """
    Dependency for admin-only endpoints.
    """
    return require_role(UserRole.ADMIN)


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    db = Depends(get_database)
) -> Optional[User]:
    """
    Get the current user if authenticated, otherwise return None.
    Useful for endpoints that work with or without authentication.
    """
    if credentials is None:
        return None
    
    try:
        token = credentials.credentials
        payload = verify_token(token)
        
        if payload is None:
            return None
        
        user_id = payload.get("sub")
        if user_id is None:
            return None
        
        user_doc = await db.users.find_one({"_id": user_id})
        if user_doc is None:
            return None
        
        user = User(**user_doc)
        return user if user.is_active else None
        
    except Exception as e:
        logger.debug(f"Optional authentication failed: {e}")
        return None