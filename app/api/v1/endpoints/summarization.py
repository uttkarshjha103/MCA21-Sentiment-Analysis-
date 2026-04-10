"""
Text Summarization API endpoints.
Provides endpoints for generating summaries with configurable parameters.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from app.services.summarization import (
    get_text_summarizer,
    TextSummarizer,
    SummaryParams,
    SummaryLength
)
from .auth import get_current_user
from app.models.user import User
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


class SummarizationRequest(BaseModel):
    """Request model for text summarization."""
    texts: List[str] = Field(..., description="List of texts to summarize")
    max_length: int = Field(default=150, ge=20, le=500, description="Maximum summary length")
    min_length: int = Field(default=40, ge=10, le=200, description="Minimum summary length")


class LengthPresetRequest(BaseModel):
    """Request model for summarization using a length preset."""
    texts: List[str] = Field(..., description="List of texts to summarize")
    length: str = Field(
        default="medium",
        description="Summary length preset: 'short', 'medium', or 'long'"
    )


class CustomSummarizationRequest(BaseModel):
    """Request model for summarization with custom parameters."""
    texts: List[str] = Field(..., description="List of texts to summarize")
    max_length: int = Field(default=150, ge=20, le=500, description="Maximum summary length")
    min_length: int = Field(default=40, ge=10, le=200, description="Minimum summary length")
    length_penalty: float = Field(default=2.0, ge=0.5, le=5.0, description="Length penalty for generation")
    num_beams: int = Field(default=4, ge=1, le=10, description="Number of beams for beam search")
    early_stopping: bool = Field(default=True, description="Whether to stop generation early")


class RegenerateSummaryRequest(BaseModel):
    """Request model for regenerating summary with different parameters."""
    texts: List[str] = Field(..., description="List of texts to summarize")
    max_length: int = Field(..., ge=20, le=500, description="New maximum summary length")
    min_length: int = Field(..., ge=10, le=200, description="New minimum summary length")
    length_penalty: Optional[float] = Field(default=2.0, ge=0.5, le=5.0, description="Length penalty")
    num_beams: Optional[int] = Field(default=4, ge=1, le=10, description="Number of beams")


class SummaryResponse(BaseModel):
    """Response model for summarization result."""
    summary_text: str = Field(..., description="Generated summary text")
    original_length: int = Field(..., description="Total length of original texts")
    summary_length: int = Field(..., description="Length of generated summary")
    params: Dict[str, Any] = Field(..., description="Parameters used for generation")
    model_version: str = Field(..., description="Model version used")
    generated_at: str = Field(..., description="Timestamp when summary was generated")


class ModelInfoResponse(BaseModel):
    """Response model for model information."""
    model_name: str
    device: str
    model_type: str


@router.post("/generate", response_model=SummaryResponse, status_code=status.HTTP_200_OK)
async def generate_summary(
    request: SummarizationRequest,
    current_user: User = Depends(get_current_user),
    summarizer: TextSummarizer = Depends(get_text_summarizer)
):
    """
    Generate a summary from a collection of texts.
    
    Requires authentication. Uses T5 model to generate coherent summaries
    with configurable length parameters.
    """
    try:
        logger.info(f"User {current_user.email} requested summary generation for {len(request.texts)} texts")
        
        if not request.texts:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No texts provided for summarization"
            )
        
        result = summarizer.generate_summary(
            request.texts,
            max_length=request.max_length,
            min_length=request.min_length
        )
        
        return SummaryResponse(**result.to_dict())
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating summary: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate summary: {str(e)}"
        )


@router.post("/generate/by-length", response_model=SummaryResponse, status_code=status.HTTP_200_OK)
async def generate_summary_by_length(
    request: LengthPresetRequest,
    current_user: User = Depends(get_current_user),
    summarizer: TextSummarizer = Depends(get_text_summarizer)
):
    """
    Generate a summary using a predefined length preset.
    
    Requires authentication. Accepts 'short', 'medium', or 'long' as the length
    parameter to control summary verbosity without specifying exact token counts.
    """
    try:
        logger.info(f"User {current_user.email} requested {request.length} summary for {len(request.texts)} texts")

        if not request.texts:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No texts provided for summarization"
            )

        valid_lengths = [SummaryLength.SHORT, SummaryLength.MEDIUM, SummaryLength.LONG]
        if request.length not in valid_lengths:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid length preset '{request.length}'. Must be one of: {valid_lengths}"
            )

        result = summarizer.generate_summary_by_length(request.texts, request.length)
        return SummaryResponse(**result.to_dict())
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating summary by length: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate summary: {str(e)}"
        )


@router.post("/generate/custom", response_model=SummaryResponse, status_code=status.HTTP_200_OK)
async def generate_custom_summary(
    request: CustomSummarizationRequest,
    current_user: User = Depends(get_current_user),
    summarizer: TextSummarizer = Depends(get_text_summarizer)
):
    """
    Generate a summary with custom parameters.
    
    Requires authentication. Provides fine-grained control over summarization
    parameters including length penalty, beam search, and early stopping.
    """
    try:
        logger.info(f"User {current_user.email} requested custom summary generation")
        
        if not request.texts:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No texts provided for summarization"
            )
        
        params = SummaryParams(
            max_length=request.max_length,
            min_length=request.min_length,
            length_penalty=request.length_penalty,
            num_beams=request.num_beams,
            early_stopping=request.early_stopping
        )
        
        result = summarizer.generate_custom_summary(request.texts, params)
        
        return SummaryResponse(**result.to_dict())
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating custom summary: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate custom summary: {str(e)}"
        )


@router.post("/regenerate", response_model=SummaryResponse, status_code=status.HTTP_200_OK)
async def regenerate_summary(
    request: RegenerateSummaryRequest,
    current_user: User = Depends(get_current_user),
    summarizer: TextSummarizer = Depends(get_text_summarizer)
):
    """
    Regenerate a summary with different parameters.
    
    Requires authentication. Allows users to regenerate summaries with
    different length constraints or generation parameters.
    """
    try:
        logger.info(f"User {current_user.email} requested summary regeneration")
        
        if not request.texts:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No texts provided for summarization"
            )
        
        params = SummaryParams(
            max_length=request.max_length,
            min_length=request.min_length,
            length_penalty=request.length_penalty,
            num_beams=request.num_beams
        )
        
        result = summarizer.regenerate_summary(request.texts, params)
        
        return SummaryResponse(**result.to_dict())
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error regenerating summary: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to regenerate summary: {str(e)}"
        )


@router.get("/model-info", response_model=ModelInfoResponse, status_code=status.HTTP_200_OK)
async def get_model_info(
    current_user: User = Depends(get_current_user),
    summarizer: TextSummarizer = Depends(get_text_summarizer)
):
    """
    Get information about the summarization model.
    
    Requires authentication. Returns model name, device, and model type.
    """
    try:
        info = summarizer.get_model_info()
        return ModelInfoResponse(**info)
    except Exception as e:
        logger.error(f"Error getting model info: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get model info: {str(e)}"
        )
