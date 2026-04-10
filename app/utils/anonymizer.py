"""
Data anonymization utilities for masking PII in comment text.

Supports masking of:
- Email addresses
- Phone numbers (Indian and international formats)
- Aadhaar numbers (12-digit Indian national ID)
- PAN card numbers (Indian tax ID)
- IP addresses
- URLs / web links
- Generic numeric sequences that look like IDs

Validates: Requirements 10.4
"""
import re
import logging
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# PII patterns
# ---------------------------------------------------------------------------

_PATTERNS: dict[str, re.Pattern] = {
    "email": re.compile(
        r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}",
        re.IGNORECASE,
    ),
    "phone_in": re.compile(
        # Indian mobile: optional +91 / 0, then 10 digits starting with 6-9
        r"(?:\+91[\s\-]?|0)?[6-9]\d{9}",
    ),
    "phone_intl": re.compile(
        # Generic international: +<country_code> <digits>
        r"\+\d{1,3}[\s\-]?\(?\d{1,4}\)?[\s\-]?\d{3,4}[\s\-]?\d{4}",
    ),
    "aadhaar": re.compile(
        # 12-digit number, optionally space/hyphen separated in groups of 4
        r"\b\d{4}[\s\-]?\d{4}[\s\-]?\d{4}\b",
    ),
    "pan": re.compile(
        # Indian PAN: 5 letters, 4 digits, 1 letter
        r"\b[A-Z]{5}\d{4}[A-Z]\b",
    ),
    "ip_address": re.compile(
        r"\b(?:\d{1,3}\.){3}\d{1,3}\b",
    ),
    "url": re.compile(
        r"https?://[^\s]+",
        re.IGNORECASE,
    ),
}

# Replacement tokens for each PII type
_REPLACEMENTS: dict[str, str] = {
    "email": "[EMAIL]",
    "phone_in": "[PHONE]",
    "phone_intl": "[PHONE]",
    "aadhaar": "[AADHAAR]",
    "pan": "[PAN]",
    "ip_address": "[IP_ADDRESS]",
    "url": "[URL]",
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

@dataclass
class AnonymizationResult:
    """Result of an anonymization operation."""
    original_text: str
    anonymized_text: str
    pii_found: dict[str, int] = field(default_factory=dict)

    @property
    def has_pii(self) -> bool:
        return bool(self.pii_found)

    @property
    def total_replacements(self) -> int:
        return sum(self.pii_found.values())


def anonymize_text(
    text: str,
    mask_email: bool = True,
    mask_phone: bool = True,
    mask_aadhaar: bool = True,
    mask_pan: bool = True,
    mask_ip: bool = True,
    mask_url: bool = False,
) -> AnonymizationResult:
    """
    Mask PII patterns in *text* and return an :class:`AnonymizationResult`.

    Args:
        text: The input comment text.
        mask_email: Replace email addresses with ``[EMAIL]``.
        mask_phone: Replace phone numbers with ``[PHONE]``.
        mask_aadhaar: Replace Aadhaar numbers with ``[AADHAAR]``.
        mask_pan: Replace PAN card numbers with ``[PAN]``.
        mask_ip: Replace IP addresses with ``[IP_ADDRESS]``.
        mask_url: Replace URLs with ``[URL]`` (off by default).

    Returns:
        :class:`AnonymizationResult` with the anonymized text and counts.
    """
    if not text:
        return AnonymizationResult(original_text=text, anonymized_text=text)

    result_text = text
    pii_found: dict[str, int] = {}

    active_patterns: list[tuple[str, re.Pattern, str]] = []
    if mask_email:
        active_patterns.append(("email", _PATTERNS["email"], _REPLACEMENTS["email"]))
    if mask_phone:
        active_patterns.append(("phone_in", _PATTERNS["phone_in"], _REPLACEMENTS["phone_in"]))
        active_patterns.append(("phone_intl", _PATTERNS["phone_intl"], _REPLACEMENTS["phone_intl"]))
    if mask_aadhaar:
        active_patterns.append(("aadhaar", _PATTERNS["aadhaar"], _REPLACEMENTS["aadhaar"]))
    if mask_pan:
        active_patterns.append(("pan", _PATTERNS["pan"], _REPLACEMENTS["pan"]))
    if mask_ip:
        active_patterns.append(("ip_address", _PATTERNS["ip_address"], _REPLACEMENTS["ip_address"]))
    if mask_url:
        active_patterns.append(("url", _PATTERNS["url"], _REPLACEMENTS["url"]))

    for pii_type, pattern, replacement in active_patterns:
        matches = pattern.findall(result_text)
        if matches:
            count = len(matches)
            # Merge phone_in / phone_intl under a single "phone" key for reporting
            report_key = "phone" if pii_type.startswith("phone") else pii_type
            pii_found[report_key] = pii_found.get(report_key, 0) + count
            result_text = pattern.sub(replacement, result_text)

    return AnonymizationResult(
        original_text=text,
        anonymized_text=result_text,
        pii_found=pii_found,
    )


def anonymize_comment_dict(
    comment: dict,
    text_field: str = "comment_text",
    **kwargs,
) -> dict:
    """
    Return a *copy* of *comment* with PII masked in *text_field*.

    Extra keyword arguments are forwarded to :func:`anonymize_text`.
    """
    if text_field not in comment:
        return comment.copy()

    result = anonymize_text(comment[text_field], **kwargs)
    anonymized = comment.copy()
    anonymized[text_field] = result.anonymized_text
    anonymized["_anonymized"] = True
    anonymized["_pii_found"] = result.pii_found
    return anonymized
