"""
Custom exceptions for the MCA21 Sentiment Analysis System.
"""
from typing import Any, Dict, Optional
from fastapi import HTTPException, status


class MCA21Exception(Exception):
    """Base exception for MCA21 system."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class AuthenticationError(MCA21Exception):
    """Authentication related errors."""
    pass


class AuthorizationError(MCA21Exception):
    """Authorization related errors."""
    pass


class ValidationError(MCA21Exception):
    """Data validation errors."""
    pass


class ProcessingError(MCA21Exception):
    """AI processing related errors."""
    pass


class DatabaseError(MCA21Exception):
    """Database operation errors."""
    pass


class FileProcessingError(MCA21Exception):
    """File upload and processing errors."""
    pass


# HTTP Exception helpers
def create_http_exception(
    status_code: int,
    message: str,
    details: Optional[Dict[str, Any]] = None
) -> HTTPException:
    """Create a standardized HTTP exception."""
    return HTTPException(
        status_code=status_code,
        detail={
            "message": message,
            "details": details or {},
            "error_code": f"MCA21_{status_code}"
        }
    )


def authentication_exception(message: str = "Authentication failed") -> HTTPException:
    """Create authentication exception."""
    return create_http_exception(
        status_code=status.HTTP_401_UNAUTHORIZED,
        message=message,
        details={"headers": {"WWW-Authenticate": "Bearer"}}
    )


def authorization_exception(message: str = "Insufficient permissions") -> HTTPException:
    """Create authorization exception."""
    return create_http_exception(
        status_code=status.HTTP_403_FORBIDDEN,
        message=message
    )


def validation_exception(message: str, details: Optional[Dict[str, Any]] = None) -> HTTPException:
    """Create validation exception."""
    return create_http_exception(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        message=message,
        details=details
    )


def not_found_exception(resource: str = "Resource") -> HTTPException:
    """Create not found exception."""
    return create_http_exception(
        status_code=status.HTTP_404_NOT_FOUND,
        message=f"{resource} not found"
    )


def server_error_exception(message: str = "Internal server error") -> HTTPException:
    """Create server error exception."""
    return create_http_exception(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        message=message
    )