"""
Report-related Pydantic models.
"""
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class ReportFilters(BaseModel):
    """Filters applied when generating a report."""
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    sentiment: Optional[str] = None
    language: Optional[str] = None
    source: Optional[str] = None
    keywords: Optional[List[str]] = None


class ReportCreate(BaseModel):
    """Request model for creating a report."""
    title: str = Field(..., min_length=1, max_length=200)
    report_type: str = Field(..., pattern="^(excel|csv)$")
    filters: Optional[ReportFilters] = None
    include_metadata: bool = True


class ReportResponse(BaseModel):
    """Report status and metadata response."""
    report_id: str
    title: str
    report_type: str
    status: str
    generated_by: str
    generated_at: datetime
    completed_at: Optional[datetime] = None
    file_path: Optional[str] = None
    download_url: Optional[str] = None
    filters_applied: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None

    class Config:
        populate_by_name = True
