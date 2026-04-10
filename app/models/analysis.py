"""
Analysis-related Pydantic models for sentiment, keywords, and summaries.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class SentimentResult(BaseModel):
    """Sentiment analysis result model."""
    label: str = Field(..., pattern="^(positive|negative|neutral)$")
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    model_version: str
    processed_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_schema_extra = {
            "example": {
                "label": "positive",
                "confidence_score": 0.89,
                "model_version": "roberta-base-v1.0",
                "processed_at": "2024-01-15T10:30:00Z"
            }
        }


class Keyword(BaseModel):
    """Keyword extraction result model."""
    text: str = Field(..., min_length=1, max_length=100)
    frequency: int = Field(..., ge=1)
    tfidf_score: float = Field(..., ge=0.0)
    topic_cluster: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "text": "policy implementation",
                "frequency": 15,
                "tfidf_score": 0.75,
                "topic_cluster": "governance"
            }
        }


class TopicCluster(BaseModel):
    """Topic clustering result model."""
    cluster_id: str
    cluster_name: str
    keywords: List[str]
    comment_count: int
    representative_comments: List[str] = Field(max_length=5)


class Summary(BaseModel):
    """Text summarization result model."""
    summary_id: str = Field(alias="_id")
    original_comment_ids: List[str]
    summary_text: str = Field(..., min_length=10, max_length=2000)
    summary_length: int
    model_version: str
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    parameters: Optional[Dict[str, Any]] = None
    
    class Config:
        populate_by_name = True


class AnalysisResult(BaseModel):
    """Complete analysis result for a comment or batch of comments."""
    comment_ids: List[str]
    sentiment_results: List[SentimentResult]
    keywords: List[Keyword]
    summary: Optional[Summary] = None
    topic_clusters: Optional[List[TopicCluster]] = None
    processing_time: float = Field(..., description="Processing time in seconds")


class AnalysisRequest(BaseModel):
    """Request model for analysis operations."""
    comment_ids: List[str]
    include_sentiment: bool = True
    include_keywords: bool = True
    include_summary: bool = False
    include_clustering: bool = False
    summary_max_length: int = Field(default=150, ge=50, le=500)
    num_clusters: int = Field(default=5, ge=2, le=20)


class BatchAnalysisStatus(BaseModel):
    """Status model for batch analysis operations."""
    batch_id: str
    status: str = Field(..., pattern="^(pending|processing|completed|failed)$")
    total_comments: int
    processed_comments: int
    progress_percentage: float = Field(..., ge=0.0, le=100.0)
    started_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    results: Optional[AnalysisResult] = None