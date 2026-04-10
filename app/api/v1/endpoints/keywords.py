"""
Keyword Extraction and Topic Analysis API endpoints.
Provides TF-IDF keyword extraction, RAKE phrase extraction, and K-means topic clustering.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

from app.services.keywords import (
    get_keyword_extractor,
    KeywordExtractor,
    Keyword,
    TopicCluster,
    TFIDFResult,
    KeywordExtractionResult,
)
from .auth import get_current_user
from app.models.user import User
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class KeywordRequest(BaseModel):
    """Request model for keyword extraction."""
    texts: List[str] = Field(..., description="List of text documents to analyse")
    top_n: Optional[int] = Field(default=30, ge=1, le=100, description="Max keywords to return")


class RAKERequest(BaseModel):
    """Request model for RAKE phrase extraction."""
    texts: List[str] = Field(..., description="List of text documents to analyse")
    top_n: Optional[int] = Field(default=15, ge=1, le=50, description="Max phrases to return")


class AnalyzeRequest(BaseModel):
    """Request model for full keyword analysis (TF-IDF + RAKE + clustering)."""
    texts: List[str] = Field(..., description="List of text documents to analyse")
    top_n_keywords: Optional[int] = Field(default=30, ge=1, le=100, description="Max TF-IDF keywords")
    top_n_phrases: Optional[int] = Field(default=15, ge=1, le=50, description="Max RAKE phrases")
    n_clusters: Optional[int] = Field(default=5, ge=2, le=20, description="Number of topic clusters")


class KeywordResponse(BaseModel):
    """Response model for a single keyword."""
    text: str
    frequency: int
    tfidf_score: float
    topic_cluster: Optional[str] = None


class TopicClusterResponse(BaseModel):
    """Response model for a topic cluster."""
    cluster_id: str
    keywords: List[str]
    centroid_terms: List[str]


class TFIDFResponse(BaseModel):
    """Response model for TF-IDF computation results."""
    keywords: List[KeywordResponse]
    vocabulary_size: int
    document_count: int
    computed_at: str


class RAKEResponse(BaseModel):
    """Response model for RAKE phrase extraction."""
    phrases: List[Dict[str, Any]]
    document_count: int


class FullAnalysisResponse(BaseModel):
    """Response model for full keyword analysis."""
    tfidf_keywords: List[KeywordResponse]
    rake_phrases: List[Dict[str, Any]]
    topic_clusters: List[TopicClusterResponse]
    document_count: int
    extracted_at: str


class ExtractorInfoResponse(BaseModel):
    """Response model for extractor configuration info."""
    top_n_keywords: int
    top_n_phrases: int
    n_clusters: int
    algorithms: List[str]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/tfidf", response_model=TFIDFResponse, status_code=status.HTTP_200_OK)
async def extract_tfidf_keywords(
    request: KeywordRequest,
    current_user: User = Depends(get_current_user),
    extractor: KeywordExtractor = Depends(get_keyword_extractor),
):
    """
    Extract keywords using TF-IDF scoring.

    Requires authentication. Returns keywords ranked by their TF-IDF score
    across the provided document corpus.
    """
    try:
        logger.info(
            f"User {current_user.email} requested TF-IDF extraction for {len(request.texts)} texts"
        )
        if not request.texts:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No texts provided for keyword extraction",
            )

        # Temporarily override top_n if caller specified it
        extractor.top_n_keywords = request.top_n or extractor.top_n_keywords
        result: TFIDFResult = extractor.calculate_tfidf_scores(request.texts)

        return TFIDFResponse(
            keywords=[KeywordResponse(**kw.to_dict()) for kw in result.keywords],
            vocabulary_size=result.vocabulary_size,
            document_count=result.document_count,
            computed_at=result.computed_at.isoformat(),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error extracting TF-IDF keywords: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to extract keywords: {e}",
        )


@router.post("/rake", response_model=RAKEResponse, status_code=status.HTTP_200_OK)
async def extract_rake_phrases(
    request: RAKERequest,
    current_user: User = Depends(get_current_user),
    extractor: KeywordExtractor = Depends(get_keyword_extractor),
):
    """
    Extract multi-word phrases using the RAKE algorithm.

    Requires authentication. Returns candidate phrases ranked by their
    RAKE score (word degree / word frequency).
    """
    try:
        logger.info(
            f"User {current_user.email} requested RAKE extraction for {len(request.texts)} texts"
        )
        if not request.texts:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No texts provided for phrase extraction",
            )

        extractor.top_n_phrases = request.top_n or extractor.top_n_phrases
        phrases = extractor.extract_rake_phrases(request.texts)
        clean_count = sum(1 for t in request.texts if t and t.strip())

        return RAKEResponse(phrases=phrases, document_count=clean_count)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error extracting RAKE phrases: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to extract phrases: {e}",
        )


@router.post("/analyze", response_model=FullAnalysisResponse, status_code=status.HTTP_200_OK)
async def analyze_keywords(
    request: AnalyzeRequest,
    current_user: User = Depends(get_current_user),
    extractor: KeywordExtractor = Depends(get_keyword_extractor),
):
    """
    Full keyword extraction and topic analysis pipeline.

    Requires authentication. Runs TF-IDF keyword extraction, RAKE phrase
    extraction, and K-means topic clustering in a single request.
    """
    try:
        logger.info(
            f"User {current_user.email} requested full keyword analysis for {len(request.texts)} texts"
        )
        if not request.texts:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No texts provided for analysis",
            )

        # Apply caller-specified parameters
        if request.top_n_keywords:
            extractor.top_n_keywords = request.top_n_keywords
        if request.top_n_phrases:
            extractor.top_n_phrases = request.top_n_phrases
        if request.n_clusters:
            extractor.n_clusters = request.n_clusters

        result: KeywordExtractionResult = extractor.analyze(request.texts)

        return FullAnalysisResponse(
            tfidf_keywords=[KeywordResponse(**kw.to_dict()) for kw in result.tfidf_keywords],
            rake_phrases=result.rake_phrases,
            topic_clusters=[TopicClusterResponse(**tc.to_dict()) for tc in result.topic_clusters],
            document_count=result.document_count,
            extracted_at=result.extracted_at.isoformat(),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error running keyword analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to run keyword analysis: {e}",
        )


@router.get("/info", response_model=ExtractorInfoResponse, status_code=status.HTTP_200_OK)
async def get_extractor_info(
    current_user: User = Depends(get_current_user),
    extractor: KeywordExtractor = Depends(get_keyword_extractor),
):
    """
    Get configuration information about the keyword extractor.

    Requires authentication.
    """
    try:
        info = extractor.get_info()
        return ExtractorInfoResponse(**info)
    except Exception as e:
        logger.error(f"Error getting extractor info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get extractor info: {e}",
        )
