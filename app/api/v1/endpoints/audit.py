"""
Audit log endpoints for viewing system activity.
"""
import logging
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from motor.motor_asyncio import AsyncIOMotorDatabase

from ....core.database import get_database
from ....models.user import User, UserRole
from ....models.audit import AuditLogQuery, AuditLogResponse, AuditAction
from ....services.audit import AuditLogger, get_audit_logger
from .auth import get_current_user, get_current_admin_user

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/logs", response_model=AuditLogResponse)
async def get_audit_logs(
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    action: Optional[AuditAction] = Query(None, description="Filter by action type"),
    start_date: Optional[datetime] = Query(None, description="Filter by start date"),
    end_date: Optional[datetime] = Query(None, description="Filter by end date"),
    success: Optional[bool] = Query(None, description="Filter by success status"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of logs to return"),
    skip: int = Query(0, ge=0, description="Number of logs to skip"),
    current_user: User = Depends(get_current_admin_user),
    audit_logger: AuditLogger = Depends(get_audit_logger)
):
    """
    Retrieve audit logs (Admin only).
    
    Allows filtering by user, action type, date range, and success status.
    Results are paginated using limit and skip parameters.
    """
    try:
        query = AuditLogQuery(
            user_id=user_id,
            action=action,
            start_date=start_date,
            end_date=end_date,
            success=success,
            limit=limit,
            skip=skip
        )
        
        total, logs = await audit_logger.get_logs(query)
        
        return AuditLogResponse(total=total, logs=logs)
        
    except Exception as e:
        logger.error(f"Error retrieving audit logs: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve audit logs"
        )


@router.get("/logs/me")
async def get_my_activity(
    limit: int = Query(50, ge=1, le=500, description="Maximum number of logs to return"),
    current_user: User = Depends(get_current_user),
    audit_logger: AuditLogger = Depends(get_audit_logger)
):
    """
    Get audit logs for the current authenticated user.
    
    Returns recent activity for the logged-in user.
    """
    try:
        logs = await audit_logger.get_user_activity(str(current_user.id), limit)
        return {"total": len(logs), "logs": logs}
        
    except Exception as e:
        logger.error(f"Error retrieving user activity: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user activity"
        )


@router.get("/logs/user/{user_id}")
async def get_user_audit_logs(
    user_id: str,
    limit: int = Query(100, ge=1, le=500, description="Maximum number of logs to return"),
    current_user: User = Depends(get_current_admin_user),
    audit_logger: AuditLogger = Depends(get_audit_logger)
):
    """
    Get audit logs for a specific user (Admin only).
    
    Returns recent activity for the specified user ID.
    """
    try:
        logs = await audit_logger.get_user_activity(user_id, limit)
        return {"total": len(logs), "logs": logs}
        
    except Exception as e:
        logger.error(f"Error retrieving user audit logs: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user audit logs"
        )
