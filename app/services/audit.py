"""
Audit logging service for tracking user actions and data access.
"""
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from motor.motor_asyncio import AsyncIOMotorDatabase
from fastapi import Request, Depends

from ..models.audit import AuditAction, AuditLogEntry, AuditLogQuery
from ..models.user import User
from ..core.database import get_database

logger = logging.getLogger(__name__)


class AuditLogger:
    """Service for creating and managing audit logs."""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db.audit_logs
    
    async def log_action(
        self,
        action: AuditAction,
        user: Optional[User] = None,
        request: Optional[Request] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        success: bool = True,
        error_message: Optional[str] = None
    ) -> AuditLogEntry:
        """
        Log an auditable action.
        
        Args:
            action: The type of action being logged
            user: The user performing the action (if authenticated)
            request: The FastAPI request object (for IP and user agent)
            resource_type: Type of resource being accessed (e.g., "comment", "report")
            resource_id: ID of the specific resource
            details: Additional context about the action
            success: Whether the action was successful
            error_message: Error message if action failed
        
        Returns:
            The created audit log entry
        """
        # Extract request information
        ip_address = None
        user_agent = None
        if request:
            ip_address = request.client.host if request.client else None
            user_agent = request.headers.get("user-agent")
        
        # Create audit log entry
        log_entry = AuditLogEntry(
            timestamp=datetime.utcnow(),
            action=action,
            user_id=str(user.id) if user else None,
            user_email=user.email if user else None,
            user_role=user.role.value if user and hasattr(user.role, 'value') else (user.role if user else None),
            ip_address=ip_address,
            user_agent=user_agent,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            success=success,
            error_message=error_message
        )
        
        # Insert into database
        try:
            log_dict = log_entry.dict(by_alias=True, exclude={"id"})
            result = await self.collection.insert_one(log_dict)
            log_entry.id = result.inserted_id
            
            # Log to application logger as well
            log_level = logging.INFO if success else logging.WARNING
            logger.log(
                log_level,
                f"Audit: {action.value} - User: {user.email if user else 'anonymous'} - "
                f"Success: {success} - Resource: {resource_type}:{resource_id if resource_id else 'N/A'}"
            )
            
        except Exception as e:
            logger.error(f"Failed to create audit log entry: {e}")
            # Don't raise exception - audit logging should not break application flow
        
        return log_entry
    
    async def get_logs(self, query: AuditLogQuery) -> tuple[int, list[AuditLogEntry]]:
        """
        Retrieve audit logs based on query parameters.
        
        Args:
            query: Query parameters for filtering logs
        
        Returns:
            Tuple of (total_count, log_entries)
        """
        # Build MongoDB query
        filter_dict = {}
        
        if query.user_id:
            filter_dict["user_id"] = query.user_id
        
        if query.action:
            filter_dict["action"] = query.action.value
        
        if query.success is not None:
            filter_dict["success"] = query.success
        
        if query.start_date or query.end_date:
            filter_dict["timestamp"] = {}
            if query.start_date:
                filter_dict["timestamp"]["$gte"] = query.start_date
            if query.end_date:
                filter_dict["timestamp"]["$lte"] = query.end_date
        
        # Get total count
        total = await self.collection.count_documents(filter_dict)
        
        # Get logs with pagination
        cursor = self.collection.find(filter_dict).sort("timestamp", -1).skip(query.skip).limit(query.limit)
        logs = []
        async for doc in cursor:
            logs.append(AuditLogEntry(**doc))
        
        return total, logs
    
    async def get_user_activity(self, user_id: str, limit: int = 50) -> list[AuditLogEntry]:
        """
        Get recent activity for a specific user.
        
        Args:
            user_id: The user ID to query
            limit: Maximum number of entries to return
        
        Returns:
            List of audit log entries
        """
        cursor = self.collection.find({"user_id": user_id}).sort("timestamp", -1).limit(limit)
        logs = []
        async for doc in cursor:
            logs.append(AuditLogEntry(**doc))
        return logs
    
    async def get_failed_login_attempts(self, email: str, since: datetime) -> int:
        """
        Count failed login attempts for an email since a given time.
        
        Args:
            email: User email address
            since: Start time for counting attempts
        
        Returns:
            Number of failed login attempts
        """
        count = await self.collection.count_documents({
            "user_email": email,
            "action": AuditAction.LOGIN_FAILED.value,
            "timestamp": {"$gte": since}
        })
        return count
    
    async def create_indexes(self):
        """Create database indexes for efficient querying."""
        try:
            await self.collection.create_index("timestamp")
            await self.collection.create_index("user_id")
            await self.collection.create_index("action")
            await self.collection.create_index([("user_email", 1), ("timestamp", -1)])
            logger.info("Audit log indexes created successfully")
        except Exception as e:
            logger.error(f"Failed to create audit log indexes: {e}")


async def get_audit_logger(db: AsyncIOMotorDatabase = Depends(get_database)) -> AuditLogger:
    """Dependency for getting audit logger instance."""
    return AuditLogger(db)
