"""
Sentiment Analysis Service using RoBERTa model from Hugging Face.
Provides sentiment classification with confidence scoring and batch processing.
"""

from typing import List, Dict, Any, Optional
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class SentimentResult:
    """Represents the result of sentiment analysis for a single text."""
    
    def __init__(self, label: str, confidence: float, scores: Dict[str, float]):
        self.label = label
        self.confidence = confidence
        self.scores = scores
        self.processed_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format for storage/API response."""
        return {
            "label": self.label,
            "confidence": self.confidence,
            "scores": self.scores,
            "processed_at": self.processed_at.isoformat()
        }


class SentimentAnalyzer:
    """
    Sentiment analysis service using RoBERTa-base model.
    Classifies text as positive, negative, or neutral with confidence scores.
    """
    
    def __init__(self, model_name: str = "cardiffnlp/twitter-roberta-base-sentiment-latest"):
        """
        Initialize the sentiment analyzer with RoBERTa model.
        
        Args:
            model_name: Hugging Face model identifier for sentiment analysis
        """
        self.model_name = model_name
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self._model = None
        self._tokenizer = None
        self._label_mapping = {
            "LABEL_0": "negative",
            "LABEL_1": "neutral", 
            "LABEL_2": "positive"
        }
        logger.info(f"Initializing SentimentAnalyzer with model: {model_name} on device: {self.device}")
    
    def _load_model(self):
        """Lazy load the model and tokenizer."""
        if self._model is None:
            logger.info("Loading RoBERTa model and tokenizer...")
            self._tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self._model = AutoModelForSequenceClassification.from_pretrained(self.model_name)
            self._model.to(self.device)
            self._model.eval()
            logger.info("Model loaded successfully")
    
    def analyze_sentiment(self, text: str) -> SentimentResult:
        """
        Analyze sentiment of a single text.
        
        Args:
            text: Input text to analyze
            
        Returns:
            SentimentResult with label, confidence, and detailed scores
        """
        self._load_model()
        
        if not text or not text.strip():
            # Return neutral for empty text
            return SentimentResult(
                label="neutral",
                confidence=1.0,
                scores={"negative": 0.0, "neutral": 1.0, "positive": 0.0}
            )
        
        # Tokenize and prepare input
        inputs = self._tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=512,
            padding=True
        ).to(self.device)
        
        # Get model predictions
        with torch.no_grad():
            outputs = self._model(**inputs)
            scores = torch.nn.functional.softmax(outputs.logits, dim=-1)
        
        # Convert to probabilities
        scores_dict = {}
        for idx, score in enumerate(scores[0].tolist()):
            label_key = f"LABEL_{idx}"
            sentiment_label = self._label_mapping.get(label_key, label_key)
            scores_dict[sentiment_label] = round(score, 4)
        
        # Get the predicted label and confidence
        predicted_idx = torch.argmax(scores, dim=-1).item()
        predicted_label_key = f"LABEL_{predicted_idx}"
        predicted_label = self._label_mapping.get(predicted_label_key, predicted_label_key)
        confidence = scores[0][predicted_idx].item()
        
        return SentimentResult(
            label=predicted_label,
            confidence=round(confidence, 4),
            scores=scores_dict
        )
    
    def batch_analyze(self, texts: List[str], batch_size: int = 32) -> List[SentimentResult]:
        """
        Analyze sentiment for multiple texts in batches for efficiency.
        
        Args:
            texts: List of texts to analyze
            batch_size: Number of texts to process in each batch
            
        Returns:
            List of SentimentResult objects
        """
        self._load_model()
        
        if not texts:
            return []
        
        results = []
        
        # Process in batches
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]
            
            # Handle empty texts
            processed_texts = [text if text and text.strip() else " " for text in batch_texts]
            
            # Tokenize batch
            inputs = self._tokenizer(
                processed_texts,
                return_tensors="pt",
                truncation=True,
                max_length=512,
                padding=True
            ).to(self.device)
            
            # Get predictions
            with torch.no_grad():
                outputs = self._model(**inputs)
                scores = torch.nn.functional.softmax(outputs.logits, dim=-1)
            
            # Process each result in the batch
            for idx, text in enumerate(batch_texts):
                if not text or not text.strip():
                    # Empty text gets neutral sentiment
                    results.append(SentimentResult(
                        label="neutral",
                        confidence=1.0,
                        scores={"negative": 0.0, "neutral": 1.0, "positive": 0.0}
                    ))
                else:
                    # Convert scores to dict
                    scores_dict = {}
                    for label_idx, score in enumerate(scores[idx].tolist()):
                        label_key = f"LABEL_{label_idx}"
                        sentiment_label = self._label_mapping.get(label_key, label_key)
                        scores_dict[sentiment_label] = round(score, 4)
                    
                    # Get predicted label
                    predicted_idx = torch.argmax(scores[idx]).item()
                    predicted_label_key = f"LABEL_{predicted_idx}"
                    predicted_label = self._label_mapping.get(predicted_label_key, predicted_label_key)
                    confidence = scores[idx][predicted_idx].item()
                    
                    results.append(SentimentResult(
                        label=predicted_label,
                        confidence=round(confidence, 4),
                        scores=scores_dict
                    ))
            
            logger.info(f"Processed batch {i//batch_size + 1}: {len(batch_texts)} texts")
        
        return results
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the loaded model."""
        return {
            "model_name": self.model_name,
            "device": self.device,
            "labels": list(self._label_mapping.values())
        }


# Global instance for reuse across requests
_sentiment_analyzer: Optional[SentimentAnalyzer] = None


def get_sentiment_analyzer() -> SentimentAnalyzer:
    """
    Get or create the global sentiment analyzer instance.
    This ensures the model is loaded only once and reused.
    """
    global _sentiment_analyzer
    if _sentiment_analyzer is None:
        _sentiment_analyzer = SentimentAnalyzer()
    return _sentiment_analyzer
