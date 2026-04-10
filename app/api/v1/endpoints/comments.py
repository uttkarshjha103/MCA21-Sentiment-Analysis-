"""
Comments management endpoints including data anonymization.

Validates: Requirements 10.4, 10.5
"""
import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.utils.anonymizer import anonymize_text, AnonymizationResult
from app.core.database import get_database
from app.api.v1.endpoints.auth import get_current_user
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------

class AnonymizeRequest(BaseModel):
    """Request body for the anonymize endpoint."""
    texts: List[str] = Field(
        ...,
        min_length=1,
        max_length=500,
        description="List of comment texts to anonymize (max 500 items).",
    )
    mask_email: bool = Field(True, description="Mask email addresses.")
    mask_phone: bool = Field(True, description="Mask phone numbers.")
    mask_aadhaar: bool = Field(True, description="Mask Aadhaar numbers.")
    mask_pan: bool = Field(True, description="Mask PAN card numbers.")
    mask_ip: bool = Field(True, description="Mask IP addresses.")
    mask_url: bool = Field(False, description="Mask URLs (disabled by default).")


class AnonymizedItem(BaseModel):
    """Single anonymized text result."""
    original_text: str
    anonymized_text: str
    has_pii: bool
    pii_found: Dict[str, int]
    total_replacements: int


class AnonymizeResponse(BaseModel):
    """Response body for the anonymize endpoint."""
    results: List[AnonymizedItem]
    total_texts: int
    texts_with_pii: int
    total_replacements: int


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post(
    "/anonymize",
    response_model=AnonymizeResponse,
    summary="Anonymize PII in comment texts",
    status_code=status.HTTP_200_OK,
)
async def anonymize_comments(
    request: AnonymizeRequest,
    current_user: User = Depends(get_current_user),
) -> AnonymizeResponse:
    """
    Mask personally identifiable information (PII) in one or more comment texts.

    Supported PII types:
    - **Email addresses** → `[EMAIL]`
    - **Phone numbers** (Indian & international) → `[PHONE]`
    - **Aadhaar numbers** → `[AADHAAR]`
    - **PAN card numbers** → `[PAN]`
    - **IP addresses** → `[IP_ADDRESS]`
    - **URLs** → `[URL]` *(opt-in via `mask_url=true`)*

    Returns the anonymized texts along with counts of PII found per type.

    **Validates: Requirements 10.4**
    """
    results: List[AnonymizedItem] = []
    texts_with_pii = 0
    total_replacements = 0

    for text in request.texts:
        result: AnonymizationResult = anonymize_text(
            text,
            mask_email=request.mask_email,
            mask_phone=request.mask_phone,
            mask_aadhaar=request.mask_aadhaar,
            mask_pan=request.mask_pan,
            mask_ip=request.mask_ip,
            mask_url=request.mask_url,
        )
        if result.has_pii:
            texts_with_pii += 1
        total_replacements += result.total_replacements

        results.append(
            AnonymizedItem(
                original_text=result.original_text,
                anonymized_text=result.anonymized_text,
                has_pii=result.has_pii,
                pii_found=result.pii_found,
                total_replacements=result.total_replacements,
            )
        )

    logger.info(
        f"Anonymization: user={current_user.email}, texts={len(request.texts)}, "
        f"texts_with_pii={texts_with_pii}, total_replacements={total_replacements}"
    )

    return AnonymizeResponse(
        results=results,
        total_texts=len(request.texts),
        texts_with_pii=texts_with_pii,
        total_replacements=total_replacements,
    )
