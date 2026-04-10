"""
Audit log models for tracking user actions and data access.
"""
from datetime import datetime
from enum import Enum
from typing import Any, Optional, Dict
from pydantic import BaseModel, Field


class AuditAction(str, Enum):
    """Types of auditable actions."""
    # Authentication actions
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILED = "login_failed"
    LOGOUT = "logout"
    REGISTER = "register"
    TOKEN_REFRESH = "token_refresh"
    
    # User management actions
    USER_CREATED = "user_created"
    USER_UPDATED = "user_updated"
    USER_DELETED = "user_deleted"
    USER_DEACTIVATED = "user_deactivated"
    USER_ACTIVATED = "user_activated"
    ACCOUNT_LOCKED = "account_locked"
    ACCOUNT_UNLOCKED = "account_unlocked"
    PASSWORD_CHANGED = "password_changed"
    
    # Data access actions
    COMMENT_UPLOADED = "comment_uploaded"
    COMMENT_VIEWED = "comment_viewed"
    COMMENT_UPDATED = "comment_updated"
    COMMENT_DELETED = "comment_deleted"
    BULK_UPLOAD = "bulk_upload"
    
    # Analysis actions
    SENTIMENT_ANALYSIS = "sentiment_analysis"
    SUMMARIZATION = "summarization"
    KEYWORD_EXTRACTION = "keyword_extraction"
    
    # Report actions
    REPORT_GENERATED = "report_generated"
    REPORT_DOWNLOADED = "report_downloaded"
    DATA_EXPORTED = "data_exported"
    
    # System actions
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    PERMISSION_DENIED = "permission_denied"


class AuditLogEntry(BaseModel):
    """Audit log entry model."""
    id: Optional[Any] = Field(default=None, alias="_id")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    action: AuditAction
    user_id: Optional[str] = None
    user_email: Optional[str] = None
    user_role: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    success: bool = True
    error_message: Optional[str] = None
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True


class AuditLogQuery(BaseModel):
    """Query parameters for audit log retrieval."""
    user_id: Optional[str] = None
    action: Optional[AuditAction] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    success: Optional[bool] = None
    limit: int = Field(default=100, ge=1, le=1000)
    skip: int = Field(default=0, ge=0)


class AuditLogResponse(BaseModel):
    """Response model for audit log queries."""
    total: int
    logs: list[AuditLogEntry]
