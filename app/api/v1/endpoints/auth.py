"""
Authentication endpoints for user registration and login.
"""
import logging
from datetime import datetime, timedelta
from typing import Optional, Annotated
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from motor.motor_asyncio import AsyncIOMotorDatabase

from ....core.database import get_database
from ....core.security import (
    verify_password, 
    get_password_hash, 
    create_access_token,
    verify_token,
    validate_password_strength
)
from ....models.user import (
    User, 
    UserCreate, 
    UserLogin, 
    UserResponse, 
    TokenResponse,
    UserRole
)
from ....models.audit import AuditAction
from ....services.audit import AuditLogger, get_audit_logger
from ....core.exceptions import MCA21Exception

logger = logging.getLogger(__name__)
router = APIRouter()
security = HTTPBearer()

# Account lockout settings
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_DURATION_MINUTES = 30


async def get_user_by_email(db: AsyncIOMotorDatabase, email: str) -> Optional[User]:
    """Get user by email address."""
    user_doc = await db.users.find_one({"email": email})
    if user_doc:
        return User(**user_doc)
    return None


async def create_user_in_db(
    db: AsyncIOMotorDatabase, 
    user: UserCreate,
    audit_logger: AuditLogger,
    request: Request
) -> User:
    """Create a new user in the database."""
    # Check if user already exists
    existing_user = await get_user_by_email(db, user.email)
    if existing_user:
        await audit_logger.log_action(
            action=AuditAction.REGISTER,
            request=request,
            details={"email": user.email, "reason": "email_already_exists"},
            success=False,
            error_message="User with this email already exists"
        )
        raise MCA21Exception(
            message="User with this email already exists",
            details={"email": user.email}
        )
    
    # Validate password strength
    is_valid, error_message = validate_password_strength(user.password)
    if not is_valid:
        await audit_logger.log_action(
            action=AuditAction.REGISTER,
            request=request,
            details={"email": user.email, "reason": "weak_password"},
            success=False,
            error_message=error_message
        )
        raise MCA21Exception(
            message="Password does not meet security requirements",
            details={"error": error_message}
        )
    
    # Create user document
    user_doc = {
        "name": user.name,
        "email": user.email,
        "password_hash": get_password_hash(user.password),
        "role": user.role.value if hasattr(user.role, 'value') else user.role,
        "created_at": datetime.utcnow(),
        "is_active": True,
        "failed_login_attempts": 0,
        "locked_until": None
    }
    
    # Insert user into database
    result = await db.users.insert_one(user_doc)
    user_doc["_id"] = result.inserted_id
    
    created_user = User(**user_doc)
    
    # Log successful registration
    await audit_logger.log_action(
        action=AuditAction.REGISTER,
        user=created_user,
        request=request,
        details={"role": user.role.value if hasattr(user.role, 'value') else user.role},
        success=True
    )
    
    logger.info(f"Created new user: {user.email} with role: {user.role}")
    return created_user


async def authenticate_user(
    db: AsyncIOMotorDatabase, 
    email: str, 
    password: str,
    audit_logger: AuditLogger,
    request: Request
) -> Optional[User]:
    """Authenticate user with email and password."""
    user = await get_user_by_email(db, email)
    if not user:
        await audit_logger.log_action(
            action=AuditAction.LOGIN_FAILED,
            request=request,
            details={"email": email, "reason": "user_not_found"},
            success=False,
            error_message="User not found"
        )
        return None
    
    # Check if account is locked
    if user.locked_until and user.locked_until > datetime.utcnow():
        await audit_logger.log_action(
            action=AuditAction.LOGIN_FAILED,
            user=user,
            request=request,
            details={"reason": "account_locked", "locked_until": user.locked_until.isoformat()},
            success=False,
            error_message="Account is locked"
        )
        raise MCA21Exception(
            message="Account is temporarily locked due to too many failed login attempts",
            details={"locked_until": user.locked_until.isoformat()}
        )
    
    # Check if account is active
    if not user.is_active:
        await audit_logger.log_action(
            action=AuditAction.LOGIN_FAILED,
            user=user,
            request=request,
            details={"reason": "account_inactive"},
            success=False,
            error_message="Account is inactive"
        )
        raise MCA21Exception(
            message="Account is deactivated",
            details={"email": email}
        )
    
    # Verify password
    if not verify_password(password, user.password_hash):
        # Increment failed login attempts
        failed_attempts = user.failed_login_attempts + 1
        update_data = {"failed_login_attempts": failed_attempts}
        
        # Lock account if too many failed attempts
        if failed_attempts >= MAX_FAILED_ATTEMPTS:
            lockout_until = datetime.utcnow() + timedelta(minutes=LOCKOUT_DURATION_MINUTES)
            update_data["locked_until"] = lockout_until
            logger.warning(f"Account locked for user {email} due to {failed_attempts} failed attempts")
            
            await audit_logger.log_action(
                action=AuditAction.ACCOUNT_LOCKED,
                user=user,
                request=request,
                details={
                    "failed_attempts": failed_attempts,
                    "locked_until": lockout_until.isoformat()
                },
                success=True
            )
        
        await db.users.update_one(
            {"_id": user.id},
            {"$set": update_data}
        )
        
        await audit_logger.log_action(
            action=AuditAction.LOGIN_FAILED,
            user=user,
            request=request,
            details={"reason": "invalid_password", "failed_attempts": failed_attempts},
            success=False,
            error_message="Invalid password"
        )
        
        return None
    
    # Reset failed login attempts on successful login
    await db.users.update_one(
        {"_id": user.id},
        {
            "$set": {
                "failed_login_attempts": 0,
                "locked_until": None,
                "last_login": datetime.utcnow()
            }
        }
    )
    
    await audit_logger.log_action(
        action=AuditAction.LOGIN_SUCCESS,
        user=user,
        request=request,
        details={"role": user.role.value if hasattr(user.role, 'value') else user.role},
        success=True
    )
    
    logger.info(f"Successful login for user: {email}")
    return user


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncIOMotorDatabase = Depends(get_database)
) -> User:
    """Get current authenticated user from JWT token."""
    token = credentials.credentials
    payload = verify_token(token)
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    email: str = payload.get("sub")
    if email is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = await get_user_by_email(db, email)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


async def get_current_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """Get current user and verify admin role."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions. Admin role required."
        )
    return current_user


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserCreate,
    request: Request,
    db: AsyncIOMotorDatabase = Depends(get_database),
    audit_logger: AuditLogger = Depends(get_audit_logger)
):
    """
    Register a new user account.
    
    - **name**: User's full name (2-100 characters)
    - **email**: Valid email address (must be unique)
    - **password**: Strong password (min 8 chars, uppercase, lowercase, digit, special char)
    - **role**: User role (admin or analyst, defaults to analyst)
    """
    try:
        # Create user in database
        user = await create_user_in_db(db, user_data, audit_logger, request)
        
        # Generate access token
        access_token_expires = timedelta(minutes=30)  # From settings
        access_token = create_access_token(
            data={"sub": user.email, "role": user.role.value if hasattr(user.role, 'value') else user.role},
            expires_delta=access_token_expires
        )
        
        # Create user response
        user_response = UserResponse(
            _id=str(user.id),
            name=user.name,
            email=user.email,
            role=user.role,
            created_at=user.created_at,
            last_login=user.last_login,
            is_active=user.is_active
        )
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=1800,  # 30 minutes in seconds
            user=user_response
        )
        
    except MCA21Exception:
        raise
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )


@router.post("/login", response_model=TokenResponse)
async def login_user(
    login_data: UserLogin,
    request: Request,
    db: AsyncIOMotorDatabase = Depends(get_database),
    audit_logger: AuditLogger = Depends(get_audit_logger)
):
    """
    Authenticate user and return access token.
    
    - **email**: User's email address
    - **password**: User's password
    
    Returns JWT access token for authenticated requests.
    """
    try:
        # Authenticate user
        user = await authenticate_user(db, login_data.email, login_data.password, audit_logger, request)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Generate access token
        access_token_expires = timedelta(minutes=30)  # From settings
        access_token = create_access_token(
            data={"sub": user.email, "role": user.role.value if hasattr(user.role, 'value') else user.role},
            expires_delta=access_token_expires
        )
        
        # Create user response
        user_response = UserResponse(
            _id=str(user.id),
            name=user.name,
            email=user.email,
            role=user.role,
            created_at=user.created_at,
            last_login=user.last_login,
            is_active=user.is_active
        )
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=1800,  # 30 minutes in seconds
            user=user_response
        )
        
    except MCA21Exception:
        raise
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    Get current authenticated user information.
    
    Requires valid JWT token in Authorization header.
    """
    return UserResponse(
        _id=str(current_user.id),
        name=current_user.name,
        email=current_user.email,
        role=current_user.role,
        created_at=current_user.created_at,
        last_login=current_user.last_login,
        is_active=current_user.is_active
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: Request,
    current_user: User = Depends(get_current_user),
    audit_logger: AuditLogger = Depends(get_audit_logger)
):
    """
    Refresh access token for authenticated user.
    
    Requires valid JWT token in Authorization header.
    Returns new access token with extended expiration.
    """
    try:
        # Log token refresh
        await audit_logger.log_action(
            action=AuditAction.TOKEN_REFRESH,
            user=current_user,
            request=request,
            success=True
        )
        
        # Generate new access token
        access_token_expires = timedelta(minutes=30)  # From settings
        access_token = create_access_token(
            data={"sub": current_user.email, "role": current_user.role.value if hasattr(current_user.role, 'value') else current_user.role},
            expires_delta=access_token_expires
        )
        
        # Create user response
        user_response = UserResponse(
            _id=str(current_user.id),
            name=current_user.name,
            email=current_user.email,
            role=current_user.role,
            created_at=current_user.created_at,
            last_login=current_user.last_login,
            is_active=current_user.is_active
        )
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=1800,  # 30 minutes in seconds
            user=user_response
        )
        
    except Exception as e:
        logger.error(f"Token refresh error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed"
        )