"""
Sentiment Analysis API endpoints.
Provides endpoints for single and batch sentiment analysis.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Dict, Any
from app.services.sentiment import get_sentiment_analyzer, SentimentAnalyzer
from .auth import get_current_user
from app.models.user import User
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


class SentimentAnalysisRequest(BaseModel):
    """Request model for single text sentiment analysis."""
    text: str = Field(..., description="Text to analyze for sentiment")


class BatchSentimentAnalysisRequest(BaseModel):
    """Request model for batch sentiment analysis."""
    texts: List[str] = Field(..., description="List of texts to analyze")
    batch_size: int = Field(default=32, ge=1, le=100, description="Batch processing size")


class SentimentResponse(BaseModel):
    """Response model for sentiment analysis result."""
    label: str = Field(..., description="Sentiment label: positive, negative, or neutral")
    confidence: float = Field(..., description="Confidence score for the prediction")
    scores: Dict[str, float] = Field(..., description="Detailed scores for all sentiment classes")
    processed_at: str = Field(..., description="Timestamp when analysis was performed")


class BatchSentimentResponse(BaseModel):
    """Response model for batch sentiment analysis."""
    results: List[SentimentResponse]
    total_processed: int
    model_info: Dict[str, Any]


class ModelInfoResponse(BaseModel):
    """Response model for model information."""
    model_name: str
    device: str
    labels: List[str]


@router.post("/analyze", response_model=SentimentResponse, status_code=status.HTTP_200_OK)
async def analyze_sentiment(
    request: SentimentAnalysisRequest,
    current_user: User = Depends(get_current_user),
    analyzer: SentimentAnalyzer = Depends(get_sentiment_analyzer)
):
    """
    Analyze sentiment of a single text.
    
    Requires authentication. Classifies text as positive, negative, or neutral
    with confidence scores using RoBERTa model.
    """
    try:
        logger.info(f"User {current_user.email} requested sentiment analysis")
        result = analyzer.analyze_sentiment(request.text)
        return SentimentResponse(**result.to_dict())
    except Exception as e:
        logger.error(f"Error analyzing sentiment: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze sentiment: {str(e)}"
        )


@router.post("/analyze/batch", response_model=BatchSentimentResponse, status_code=status.HTTP_200_OK)
async def analyze_sentiment_batch(
    request: BatchSentimentAnalysisRequest,
    current_user: User = Depends(get_current_user),
    analyzer: SentimentAnalyzer = Depends(get_sentiment_analyzer)
):
    """
    Analyze sentiment for multiple texts in batch.
    
    Requires authentication. Processes multiple texts efficiently using batch processing.
    Useful for analyzing large collections of comments.
    """
    try:
        logger.info(f"User {current_user.email} requested batch sentiment analysis for {len(request.texts)} texts")
        
        if not request.texts:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No texts provided for analysis"
            )
        
        results = analyzer.batch_analyze(request.texts, batch_size=request.batch_size)
        
        return BatchSentimentResponse(
            results=[SentimentResponse(**r.to_dict()) for r in results],
            total_processed=len(results),
            model_info=analyzer.get_model_info()
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in batch sentiment analysis: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze sentiments: {str(e)}"
        )


@router.get("/model-info", response_model=ModelInfoResponse, status_code=status.HTTP_200_OK)
async def get_model_info(
    current_user: User = Depends(get_current_user),
    analyzer: SentimentAnalyzer = Depends(get_sentiment_analyzer)
):
    """
    Get information about the sentiment analysis model.
    
    Requires authentication. Returns model name, device, and supported labels.
    """
    try:
        info = analyzer.get_model_info()
        return ModelInfoResponse(**info)
    except Exception as e:
        logger.error(f"Error getting model info: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get model info: {str(e)}"
        )
