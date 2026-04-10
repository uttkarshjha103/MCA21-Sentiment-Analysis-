"""
Text Summarization Service using T5 model from Hugging Face.
Provides text summarization with configurable parameters and regeneration support.
"""

from typing import List, Dict, Any, Optional
from transformers import T5Tokenizer, T5ForConditionalGeneration
import torch
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class SummaryParams:
    """Configuration parameters for text summarization."""
    
    def __init__(
        self,
        max_length: int = 150,
        min_length: int = 40,
        length_penalty: float = 2.0,
        num_beams: int = 4,
        early_stopping: bool = True
    ):
        self.max_length = max_length
        self.min_length = min_length
        self.length_penalty = length_penalty
        self.num_beams = num_beams
        self.early_stopping = early_stopping
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            "max_length": self.max_length,
            "min_length": self.min_length,
            "length_penalty": self.length_penalty,
            "num_beams": self.num_beams,
            "early_stopping": self.early_stopping
        }


class SummaryLength:
    """Predefined summary length presets."""
    SHORT = "short"
    MEDIUM = "medium"
    LONG = "long"

    # Preset configurations
    PRESETS: Dict[str, Dict[str, int]] = {
        "short": {"max_length": 60, "min_length": 20},
        "medium": {"max_length": 150, "min_length": 40},
        "long": {"max_length": 300, "min_length": 80},
    }

    @classmethod
    def get_params(cls, length: str) -> "SummaryParams":
        """Return SummaryParams for a given length preset."""
        preset = cls.PRESETS.get(length, cls.PRESETS["medium"])
        return SummaryParams(
            max_length=preset["max_length"],
            min_length=preset["min_length"]
        )


class SummaryResult:
    """Represents the result of text summarization."""
    
    def __init__(
        self,
        summary_text: str,
        original_length: int,
        summary_length: int,
        params: SummaryParams,
        model_version: str
    ):
        self.summary_text = summary_text
        self.original_length = original_length
        self.summary_length = summary_length
        self.params = params
        self.model_version = model_version
        self.generated_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format for storage/API response."""
        return {
            "summary_text": self.summary_text,
            "original_length": self.original_length,
            "summary_length": self.summary_length,
            "params": self.params.to_dict(),
            "model_version": self.model_version,
            "generated_at": self.generated_at.isoformat()
        }


class TextSummarizer:
    """
    Text summarization service using T5-base model.
    Generates coherent summaries with configurable length and quality parameters.
    """
    
    def __init__(self, model_name: str = "t5-base"):
        """
        Initialize the text summarizer with T5 model.
        
        Args:
            model_name: Hugging Face model identifier for summarization
        """
        self.model_name = model_name
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self._model = None
        self._tokenizer = None
        logger.info(f"Initializing TextSummarizer with model: {model_name} on device: {self.device}")
    
    def _load_model(self):
        """Lazy load the model and tokenizer."""
        if self._model is None:
            logger.info("Loading T5 model and tokenizer...")
            self._tokenizer = T5Tokenizer.from_pretrained(self.model_name)
            self._model = T5ForConditionalGeneration.from_pretrained(self.model_name)
            self._model.to(self.device)
            self._model.eval()
            logger.info("Model loaded successfully")
    
    def generate_summary(
        self,
        texts: List[str],
        max_length: int = 150,
        min_length: int = 40
    ) -> SummaryResult:
        """
        Generate a summary from a collection of texts.
        
        Args:
            texts: List of text strings to summarize
            max_length: Maximum length of the summary
            min_length: Minimum length of the summary
            
        Returns:
            SummaryResult with generated summary and metadata
        """
        params = SummaryParams(max_length=max_length, min_length=min_length)
        return self.generate_custom_summary(texts, params)
    
    def generate_custom_summary(
        self,
        texts: List[str],
        params: SummaryParams
    ) -> SummaryResult:
        """
        Generate a summary with custom parameters.
        
        Args:
            texts: List of text strings to summarize
            params: SummaryParams object with configuration
            
        Returns:
            SummaryResult with generated summary and metadata
        """
        self._load_model()
        
        if not texts or all(not text or not text.strip() for text in texts):
            # Return empty summary for empty input
            return SummaryResult(
                summary_text="",
                original_length=0,
                summary_length=0,
                params=params,
                model_version=self.model_name
            )
        
        # Combine texts into a single document
        combined_text = " ".join([text.strip() for text in texts if text and text.strip()])
        original_length = len(combined_text)
        
        # Prepare input for T5 (requires "summarize: " prefix)
        input_text = f"summarize: {combined_text}"
        
        # Tokenize input
        inputs = self._tokenizer(
            input_text,
            return_tensors="pt",
            max_length=512,
            truncation=True,
            padding=True
        ).to(self.device)
        
        # Generate summary
        with torch.no_grad():
            summary_ids = self._model.generate(
                inputs.input_ids,
                max_length=params.max_length,
                min_length=params.min_length,
                length_penalty=params.length_penalty,
                num_beams=params.num_beams,
                early_stopping=params.early_stopping
            )
        
        # Decode the summary
        summary_text = self._tokenizer.decode(summary_ids[0], skip_special_tokens=True)
        summary_length = len(summary_text)
        
        logger.info(f"Generated summary: {original_length} chars -> {summary_length} chars")
        
        return SummaryResult(
            summary_text=summary_text,
            original_length=original_length,
            summary_length=summary_length,
            params=params,
            model_version=self.model_name
        )

    
    def generate_summary_by_length(
        self,
        texts: List[str],
        length: str = "medium"
    ) -> SummaryResult:
        """
        Generate a summary using a predefined length preset.
        
        Args:
            texts: List of text strings to summarize
            length: Length preset - "short", "medium", or "long"
            
        Returns:
            SummaryResult with generated summary and metadata
        """
        params = SummaryLength.get_params(length)
        logger.info(f"Generating {length} summary with params: {params.to_dict()}")
        return self.generate_custom_summary(texts, params)

    def regenerate_summary(
        self,
        texts: List[str],
        new_params: SummaryParams
    ) -> SummaryResult:
        """
        Regenerate a summary with different parameters.
        This is a convenience method that calls generate_custom_summary.
        
        Args:
            texts: List of text strings to summarize
            new_params: New SummaryParams object with different configuration
            
        Returns:
            SummaryResult with regenerated summary
        """
        logger.info(f"Regenerating summary with new parameters: {new_params.to_dict()}")
        return self.generate_custom_summary(texts, new_params)
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the loaded model."""
        return {
            "model_name": self.model_name,
            "device": self.device,
            "model_type": "T5 (Text-to-Text Transfer Transformer)"
        }


# Global instance for reuse across requests
_text_summarizer: Optional[TextSummarizer] = None


def get_text_summarizer() -> TextSummarizer:
    """
    Get or create the global text summarizer instance.
    This ensures the model is loaded only once and reused.
    """
    global _text_summarizer
    if _text_summarizer is None:
        _text_summarizer = TextSummarizer()
    return _text_summarizer
