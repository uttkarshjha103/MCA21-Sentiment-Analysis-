"""
Language Detection and Multilingual Processing API endpoints.
Provides language detection and language-aware processing hints.

Satisfies Requirements 8.1, 8.2, 8.3, 8.4, 8.5.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

from app.services.language import (
    get_language_detector,
    LanguageDetector,
    LanguageDetectionResult,
)
from .auth import get_current_user
from app.models.user import User
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class DetectRequest(BaseModel):
    """Request model for single-text language detection."""
    text: str = Field(..., min_length=1, description="Text to detect language for")


class BatchDetectRequest(BaseModel):
    """Request model for batch language detection."""
    texts: List[str] = Field(..., description="List of texts to detect language for")


class ProcessingHintsResponse(BaseModel):
    """Language-aware processing hints for downstream services."""
    sentiment_model: str
    summarization_hint: str
    keyword_stopwords: Optional[str] = None
    rtl: bool


class DetectionResponse(BaseModel):
    """Response model for a single language detection result."""
    language_code: str
    language_name: str
    confidence: float
    script: str
    processing_hints: ProcessingHintsResponse
    detected_at: str


class BatchDetectionResponse(BaseModel):
    """Response model for batch language detection."""
    results: List[DetectionResponse]
    total: int


class SupportedLanguageItem(BaseModel):
    """A single supported language entry."""
    code: str
    name: str
    script: str


class SupportedLanguagesResponse(BaseModel):
    """Response model listing all supported languages."""
    languages: List[SupportedLanguageItem]
    total: int


class DetectorInfoResponse(BaseModel):
    """Response model for detector configuration info."""
    method: str
    supported_languages: int
    default_language: str


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _to_response(result: LanguageDetectionResult) -> DetectionResponse:
    d = result.to_dict()
    return DetectionResponse(
        language_code=d["language_code"],
        language_name=d["language_name"],
        confidence=d["confidence"],
        script=d["script"],
        processing_hints=ProcessingHintsResponse(**d["processing_hints"]),
        detected_at=d["detected_at"],
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/detect", response_model=DetectionResponse, status_code=status.HTTP_200_OK)
async def detect_language(
    text: str,
    current_user: User = Depends(get_current_user),
    detector: LanguageDetector = Depends(get_language_detector),
):
    """
    Detect the language of a text provided as a query parameter.

    Requires authentication. Returns language code, name, confidence score,
    script type, and language-aware processing hints.
    """
    try:
        if not text or not text.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Text must not be empty",
            )
        logger.info(f"User {current_user.email} requested language detection")
        result = detector.detect(text)
        return _to_response(result)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error detecting language: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Language detection failed: {e}",
        )


@router.post("/detect", response_model=DetectionResponse, status_code=status.HTTP_200_OK)
async def detect_language_post(
    request: DetectRequest,
    current_user: User = Depends(get_current_user),
    detector: LanguageDetector = Depends(get_language_detector),
):
    """
    Detect the language of a single text (POST body).

    Requires authentication. Returns language code, name, confidence score,
    script type, and language-aware processing hints.
    """
    try:
        logger.info(f"User {current_user.email} requested language detection (POST)")
        result = detector.detect(request.text)
        return _to_response(result)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error detecting language: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Language detection failed: {e}",
        )


@router.post("/detect/batch", response_model=BatchDetectionResponse, status_code=status.HTTP_200_OK)
async def detect_language_batch(
    request: BatchDetectRequest,
    current_user: User = Depends(get_current_user),
    detector: LanguageDetector = Depends(get_language_detector),
):
    """
    Detect language for a batch of texts.

    Requires authentication. Returns one detection result per input text.
    """
    try:
        if not request.texts:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No texts provided",
            )
        logger.info(
            f"User {current_user.email} requested batch language detection "
            f"for {len(request.texts)} texts"
        )
        results = detector.detect_batch(request.texts)
        return BatchDetectionResponse(
            results=[_to_response(r) for r in results],
            total=len(results),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in batch language detection: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch language detection failed: {e}",
        )


@router.get("/supported", response_model=SupportedLanguagesResponse, status_code=status.HTTP_200_OK)
async def get_supported_languages(
    current_user: User = Depends(get_current_user),
    detector: LanguageDetector = Depends(get_language_detector),
):
    """
    List all languages supported by the language detector.

    Requires authentication.
    """
    try:
        langs = detector.get_supported_languages()
        return SupportedLanguagesResponse(
            languages=[SupportedLanguageItem(**lang) for lang in langs],
            total=len(langs),
        )
    except Exception as e:
        logger.error(f"Error fetching supported languages: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch supported languages: {e}",
        )


@router.get("/info", response_model=DetectorInfoResponse, status_code=status.HTTP_200_OK)
async def get_detector_info(
    current_user: User = Depends(get_current_user),
    detector: LanguageDetector = Depends(get_language_detector),
):
    """
    Get configuration information about the language detector.

    Requires authentication.
    """
    try:
        info = detector.get_info()
        return DetectorInfoResponse(**info)
    except Exception as e:
        logger.error(f"Error getting detector info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get detector info: {e}",
        )
