"""
Comment-related Pydantic models.
"""
from datetime import datetime
from typing import Any, Optional, List, Dict
from pydantic import BaseModel, Field
from .analysis import SentimentResult, Keyword


class CommentBase(BaseModel):
    """Base comment model with common fields."""
    comment_text: str = Field(..., min_length=1, max_length=10000)
    original_language: Optional[str] = None
    source: str = Field(..., max_length=200)
    metadata: Optional[Dict[str, Any]] = None


class CommentCreate(CommentBase):
    """Comment creation model."""
    date_submitted: Optional[datetime] = None


class CommentResponse(CommentBase):
    """Comment response model."""
    comment_id: str = Field(alias="_id")
    user_id: str
    date_submitted: datetime
    processed_at: Optional[datetime] = None
    
    # Analysis results
    sentiment: Optional[SentimentResult] = None
    keywords: Optional[List[Keyword]] = None
    
    class Config:
        populate_by_name = True


class Comment(CommentBase):
    """Complete comment model for database storage."""
    comment_id: Optional[Any] = Field(default=None, alias="_id")
    user_id: Optional[Any] = None
    date_submitted: datetime = Field(default_factory=datetime.utcnow)
    processed_at: Optional[datetime] = None
    
    # Analysis results
    sentiment: Optional[SentimentResult] = None
    keywords: Optional[List[Keyword]] = None
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True


class CommentBatch(BaseModel):
    """Model for batch comment processing."""
    comments: List[CommentCreate]
    source: str = "batch_upload"
    
    class Config:
        json_schema_extra = {
            "example": {
                "comments": [
                    {
                        "comment_text": "This policy is excellent and well thought out.",
                        "source": "public_consultation_2024",
                        "date_submitted": "2024-01-15T10:30:00Z"
                    },
                    {
                        "comment_text": "I disagree with the proposed changes.",
                        "source": "public_consultation_2024",
                        "date_submitted": "2024-01-15T11:45:00Z"
                    }
                ],
                "source": "csv_upload"
            }
        }


class CommentFilter(BaseModel):
    """Model for filtering comments."""
    sentiment: Optional[str] = None
    language: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    source: Optional[str] = None
    keywords: Optional[List[str]] = None
    limit: int = Field(default=100, le=1000)
    offset: int = Field(default=0, ge=0)


class CommentStats(BaseModel):
    """Model for comment statistics."""
    total_comments: int
    sentiment_distribution: Dict[str, int]
    language_distribution: Dict[str, int]
    source_distribution: Dict[str, int]
    date_range: Dict[str, datetime]
    top_keywords: List[Dict[str, Any]]


class UploadProgress(BaseModel):
    """Model for tracking bulk upload progress."""
    upload_id: str
    user_id: str
    total_comments: int
    processed_comments: int
    stored_comments: int
    failed_comments: int
    status: str  # pending, processing, completed, failed
    errors: List[str] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    
    @property
    def progress_percentage(self) -> float:
        """Calculate progress percentage."""
        if self.total_comments == 0:
            return 0.0
        return (self.processed_comments / self.total_comments) * 100
    
    class Config:
        json_schema_extra = {
            "example": {
                "upload_id": "upload_123456",
                "user_id": "user_789",
                "total_comments": 1000,
                "processed_comments": 750,
                "stored_comments": 745,
                "failed_comments": 5,
                "status": "processing",
                "errors": ["Row 10: Invalid date format"],
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T10:35:00Z"
            }
        }