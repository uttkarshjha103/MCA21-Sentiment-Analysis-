"""
Language Detection and Multilingual Processing Service.

Implements lightweight language detection using character n-gram frequency
profiles — no external langdetect dependency required.

Supports Requirements 8.1, 8.2, 8.3, 8.4, 8.5.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import re
import logging

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Character n-gram frequency profiles for supported languages
# These are the most distinctive character bigrams/trigrams per language.
# ---------------------------------------------------------------------------

# fmt: off
_LANGUAGE_PROFILES: Dict[str, Dict[str, float]] = {
    "en": {  # English
        "th": 3.5, "he": 3.2, "in": 3.0, "er": 2.9, "an": 2.8,
        "re": 2.7, "on": 2.6, "en": 2.5, "at": 2.4, "es": 2.3,
        "ed": 2.2, "nd": 2.1, "to": 2.0, "or": 1.9, "ea": 1.8,
        "ti": 1.7, "hi": 1.6, "as": 1.5, "te": 1.4, "st": 1.3,
        "the": 5.0, "and": 4.5, "ing": 4.0, "ion": 3.5, "ent": 3.0,
        "tion": 4.5, "that": 3.5, "with": 3.0,
    },
    "de": {  # German — distinctive patterns including common function words
        "ch": 5.0, "sch": 5.5, "ung": 5.0, "ich": 4.5, "ein": 4.0,
        "und": 5.5, "der": 5.0, "die": 5.0, "das": 4.5, "ist": 4.5,
        "nicht": 4.0, "mit": 3.8, "auf": 3.5, "bei": 3.5, "von": 3.5,
        "zu": 3.0, "ge": 3.0, "ver": 3.5, "be": 2.8, "keit": 4.0,
        "heit": 4.0, "lich": 4.5, "tion": 2.0, "nen": 3.5, "ten": 3.0,
    },
    "fr": {  # French — distinctive patterns
        "qu": 4.5, "ou": 4.0, "eu": 4.0, "au": 3.8, "ai": 3.5,
        "oi": 4.0, "ez": 4.5, "ent": 4.0, "tion": 3.5, "ment": 4.5,
        "les": 5.0, "des": 5.0, "que": 5.0, "une": 4.5, "est": 4.5,
        "sur": 3.5, "par": 3.5, "pas": 3.5, "pour": 4.0, "dans": 4.0,
        "avec": 3.8, "une": 4.5, "ais": 3.5, "ait": 3.5, "ant": 3.0,
    },
    "es": {  # Spanish
        "es": 3.8, "de": 3.5, "en": 3.2, "el": 3.0, "la": 2.9,
        "os": 2.8, "on": 2.7, "ar": 2.6, "as": 2.5, "re": 2.4,
        "er": 2.3, "ue": 2.2, "ci": 2.1, "al": 2.0, "or": 1.9,
        "que": 4.5, "los": 4.0, "las": 3.8, "del": 3.5, "con": 3.2,
        "cion": 4.0, "ado": 3.0, "ando": 2.8,
    },
    "pt": {  # Portuguese
        "de": 3.8, "os": 3.5, "as": 3.2, "es": 3.0, "em": 2.9,
        "ao": 2.8, "ar": 2.7, "er": 2.6, "or": 2.5, "ue": 2.4,
        "ão": 3.5, "que": 4.0, "dos": 3.5, "das": 3.2, "com": 3.0,
        "ção": 4.5, "ado": 3.0, "ando": 2.8, "mente": 3.5,
    },
    "it": {  # Italian
        "di": 3.8, "la": 3.5, "il": 3.2, "in": 3.0, "to": 2.9,
        "re": 2.8, "er": 2.7, "on": 2.6, "ti": 2.5, "si": 2.4,
        "che": 4.5, "del": 4.0, "per": 3.8, "una": 3.5, "con": 3.2,
        "zione": 4.0, "ato": 3.0, "ando": 2.8, "mente": 3.5,
    },
    "hi": {  # Hindi (Devanagari script detection)
        "का": 4.0, "के": 3.8, "की": 3.5, "में": 3.2, "है": 3.0,
        "को": 2.8, "से": 2.6, "पर": 2.4, "यह": 2.2, "कि": 2.0,
    },
    "zh": {  # Chinese (CJK character detection)
        "的": 5.0, "是": 4.5, "在": 4.0, "了": 3.8, "和": 3.5,
        "有": 3.2, "我": 3.0, "他": 2.8, "这": 2.6, "中": 2.4,
    },
    "ar": {  # Arabic (Arabic script detection)
        "ال": 5.0, "في": 4.5, "من": 4.0, "على": 3.8, "إلى": 3.5,
        "أن": 3.2, "هذا": 3.0, "كان": 2.8, "لا": 2.6, "ما": 2.4,
    },
}
# fmt: on

# Language metadata: display name, script, and processing hints
_LANGUAGE_META: Dict[str, Dict[str, Any]] = {
    "en": {
        "name": "English",
        "script": "Latin",
        "sentiment_model": "cardiffnlp/twitter-roberta-base-sentiment-latest",
        "summarization_hint": "extractive",
        "keyword_stopwords": "english",
        "rtl": False,
    },
    "de": {
        "name": "German",
        "script": "Latin",
        "sentiment_model": "oliverguhr/german-sentiment-bert",
        "summarization_hint": "extractive",
        "keyword_stopwords": "german",
        "rtl": False,
    },
    "fr": {
        "name": "French",
        "script": "Latin",
        "sentiment_model": "nlptown/bert-base-multilingual-uncased-sentiment",
        "summarization_hint": "extractive",
        "keyword_stopwords": "french",
        "rtl": False,
    },
    "es": {
        "name": "Spanish",
        "script": "Latin",
        "sentiment_model": "nlptown/bert-base-multilingual-uncased-sentiment",
        "summarization_hint": "extractive",
        "keyword_stopwords": "spanish",
        "rtl": False,
    },
    "pt": {
        "name": "Portuguese",
        "script": "Latin",
        "sentiment_model": "nlptown/bert-base-multilingual-uncased-sentiment",
        "summarization_hint": "extractive",
        "keyword_stopwords": "portuguese",
        "rtl": False,
    },
    "it": {
        "name": "Italian",
        "script": "Latin",
        "sentiment_model": "nlptown/bert-base-multilingual-uncased-sentiment",
        "summarization_hint": "extractive",
        "keyword_stopwords": "italian",
        "rtl": False,
    },
    "hi": {
        "name": "Hindi",
        "script": "Devanagari",
        "sentiment_model": "ai4bharat/indic-bert",
        "summarization_hint": "extractive",
        "keyword_stopwords": None,
        "rtl": False,
    },
    "zh": {
        "name": "Chinese",
        "script": "CJK",
        "sentiment_model": "uer/roberta-base-finetuned-jd-binary-chinese",
        "summarization_hint": "extractive",
        "keyword_stopwords": None,
        "rtl": False,
    },
    "ar": {
        "name": "Arabic",
        "script": "Arabic",
        "sentiment_model": "CAMeL-Lab/bert-base-arabic-camelbert-da-sentiment",
        "summarization_hint": "extractive",
        "keyword_stopwords": None,
        "rtl": True,
    },
    "unknown": {
        "name": "Unknown",
        "script": "Unknown",
        "sentiment_model": "cardiffnlp/twitter-roberta-base-sentiment-latest",
        "summarization_hint": "extractive",
        "keyword_stopwords": None,
        "rtl": False,
    },
}


# ---------------------------------------------------------------------------
# Detection helpers
# ---------------------------------------------------------------------------

def _has_script(text: str, pattern: str) -> bool:
    """Return True if text contains characters matching the Unicode pattern."""
    return bool(re.search(pattern, text))


def _script_detect(text: str) -> Optional[str]:
    """
    Fast script-based detection for non-Latin languages.
    Returns a language code if a distinctive script is found, else None.
    """
    if _has_script(text, r"[\u0900-\u097F]"):  # Devanagari
        return "hi"
    if _has_script(text, r"[\u4E00-\u9FFF\u3400-\u4DBF]"):  # CJK
        return "zh"
    if _has_script(text, r"[\u0600-\u06FF]"):  # Arabic
        return "ar"
    return None


def _ngram_score(text: str, profile: Dict[str, float]) -> float:
    """
    Compute a similarity score between the text and a language profile
    by summing profile weights for each n-gram found in the text.
    """
    text_lower = text.lower()
    score = 0.0
    for ngram, weight in profile.items():
        count = text_lower.count(ngram)
        if count:
            score += weight * count
    # Normalise by text length to avoid bias toward longer texts
    return score / max(len(text_lower), 1)


def _detect_latin_language(text: str) -> str:
    """
    Detect language among Latin-script languages using n-gram profiles.
    Returns the best-matching language code.
    """
    scores: Dict[str, float] = {}
    latin_langs = [lang for lang in _LANGUAGE_PROFILES if lang not in ("hi", "zh", "ar")]
    for lang in latin_langs:
        scores[lang] = _ngram_score(text, _LANGUAGE_PROFILES[lang])

    if not scores:
        return "en"

    best = max(scores, key=lambda k: scores[k])
    # If the best score is very low, default to English
    if scores[best] < 0.01:
        return "en"
    return best


# ---------------------------------------------------------------------------
# LanguageDetectionResult
# ---------------------------------------------------------------------------

class LanguageDetectionResult:
    """Result of language detection for a single text."""

    def __init__(
        self,
        language_code: str,
        language_name: str,
        confidence: float,
        script: str,
        processing_hints: Dict[str, Any],
        detected_at: Optional[datetime] = None,
    ):
        self.language_code = language_code
        self.language_name = language_name
        self.confidence = confidence
        self.script = script
        self.processing_hints = processing_hints
        self.detected_at = detected_at or datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "language_code": self.language_code,
            "language_name": self.language_name,
            "confidence": round(self.confidence, 4),
            "script": self.script,
            "processing_hints": self.processing_hints,
            "detected_at": self.detected_at.isoformat(),
        }


# ---------------------------------------------------------------------------
# LanguageDetector – main public class
# ---------------------------------------------------------------------------

class LanguageDetector:
    """
    Lightweight language detector using character n-gram frequency profiles.

    Supports English, German, French, Spanish, Portuguese, Italian, Hindi,
    Chinese, and Arabic without any external dependencies.

    Satisfies Requirements 8.1, 8.5 (language detection and metadata storage).
    """

    SUPPORTED_LANGUAGES: List[str] = list(_LANGUAGE_META.keys())

    def __init__(self, default_language: str = "en"):
        self.default_language = default_language
        logger.info("LanguageDetector initialised (n-gram profile method)")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def detect(self, text: str) -> LanguageDetectionResult:
        """
        Detect the language of a single text.

        Args:
            text: Input text to analyse.

        Returns:
            LanguageDetectionResult with language code, name, confidence,
            script, and language-aware processing hints.
        """
        if not text or not text.strip():
            return self._build_result("unknown", 0.0)

        # Fast path: script-based detection for non-Latin scripts
        script_lang = _script_detect(text)
        if script_lang:
            return self._build_result(script_lang, 0.95)

        # N-gram profile matching for Latin-script languages
        lang = _detect_latin_language(text)
        confidence = self._estimate_confidence(text, lang)
        return self._build_result(lang, confidence)

    def detect_batch(self, texts: List[str]) -> List[LanguageDetectionResult]:
        """
        Detect language for a list of texts.

        Args:
            texts: List of input texts.

        Returns:
            List of LanguageDetectionResult objects (one per text).
        """
        return [self.detect(t) for t in texts]

    def get_processing_hints(self, language_code: str) -> Dict[str, Any]:
        """
        Return language-aware processing hints for downstream services.

        Hints include recommended sentiment model, summarization strategy,
        keyword stop-word list, and text direction.

        Args:
            language_code: ISO 639-1 language code.

        Returns:
            Dict with processing hints.
        """
        meta = _LANGUAGE_META.get(language_code, _LANGUAGE_META["unknown"])
        return {
            "sentiment_model": meta["sentiment_model"],
            "summarization_hint": meta["summarization_hint"],
            "keyword_stopwords": meta["keyword_stopwords"],
            "rtl": meta["rtl"],
        }

    def get_supported_languages(self) -> List[Dict[str, str]]:
        """Return list of supported languages with codes and names."""
        return [
            {"code": code, "name": meta["name"], "script": meta["script"]}
            for code, meta in _LANGUAGE_META.items()
            if code != "unknown"
        ]

    def get_info(self) -> Dict[str, Any]:
        """Return configuration info about this detector."""
        return {
            "method": "character_ngram_profiles",
            "supported_languages": len(self.SUPPORTED_LANGUAGES) - 1,  # exclude "unknown"
            "default_language": self.default_language,
        }

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _build_result(self, lang: str, confidence: float) -> LanguageDetectionResult:
        meta = _LANGUAGE_META.get(lang, _LANGUAGE_META["unknown"])
        hints = self.get_processing_hints(lang)
        return LanguageDetectionResult(
            language_code=lang,
            language_name=meta["name"],
            confidence=confidence,
            script=meta["script"],
            processing_hints=hints,
        )

    def _estimate_confidence(self, text: str, detected_lang: str) -> float:
        """
        Estimate detection confidence by comparing the best-match score
        against the second-best score.
        """
        latin_langs = [lang for lang in _LANGUAGE_PROFILES if lang not in ("hi", "zh", "ar")]
        scores = {lang: _ngram_score(text, _LANGUAGE_PROFILES[lang]) for lang in latin_langs}
        sorted_scores = sorted(scores.values(), reverse=True)

        if len(sorted_scores) < 2 or sorted_scores[0] == 0:
            return 0.5

        best = sorted_scores[0]
        second = sorted_scores[1]
        # Confidence = margin between best and second-best, capped at [0.5, 0.99]
        margin = (best - second) / best if best > 0 else 0.0
        return round(min(0.99, max(0.5, 0.5 + margin * 0.5)), 4)


# ---------------------------------------------------------------------------
# Global singleton
# ---------------------------------------------------------------------------

_language_detector: Optional[LanguageDetector] = None


def get_language_detector() -> LanguageDetector:
    """Return (or create) the global LanguageDetector instance."""
    global _language_detector
    if _language_detector is None:
        _language_detector = LanguageDetector()
    return _language_detector
