"""
Service layer for business logic and AI processing.
"""
# Lazy imports - don't import AI services at module level to avoid
# requiring transformers/torch at startup on Render free tier
from .upload import UploadService
from .audit import AuditLogger, get_audit_logger

__all__ = [
    "UploadService",
    "AuditLogger",
    "get_audit_logger",
]
