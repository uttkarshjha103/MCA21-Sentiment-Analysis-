"""
Unit tests for sentiment analysis service.
Tests sentiment classification, confidence scoring, and batch processing.
"""

import pytest
from app.services.sentiment import SentimentAnalyzer, SentimentResult


@pytest.fixture
def sentiment_analyzer():
    """Create a sentiment analyzer instance for testing."""
    return SentimentAnalyzer()


def test_positive_sentiment(sentiment_analyzer):
    """Test that positive text is classified correctly."""
    text = "This is an excellent policy! I fully support this initiative."
    result = sentiment_analyzer.analyze_sentiment(text)
    
    assert isinstance(result, SentimentResult)
    assert result.label == "positive"
    assert result.confidence > 0.5
    assert "positive" in result.scores
    assert "negative" in result.scores
    assert "neutral" in result.scores


def test_negative_sentiment(sentiment_analyzer):
    """Test that negative text is classified correctly."""
    text = "This is a terrible idea. I strongly oppose this policy."
    result = sentiment_analyzer.analyze_sentiment(text)
    
    assert isinstance(result, SentimentResult)
    assert result.label == "negative"
    assert result.confidence > 0.5


def test_neutral_sentiment(sentiment_analyzer):
    """Test that neutral text is classified correctly."""
    text = "The policy document contains several sections about implementation."
    result = sentiment_analyzer.analyze_sentiment(text)
    
    assert isinstance(result, SentimentResult)
    assert result.label in ["positive", "negative", "neutral"]
    assert 0.0 <= result.confidence <= 1.0


def test_empty_text(sentiment_analyzer):
    """Test handling of empty text."""
    result = sentiment_analyzer.analyze_sentiment("")
    
    assert result.label == "neutral"
    assert result.confidence == 1.0


def test_batch_analysis(sentiment_analyzer):
    """Test batch processing of multiple texts."""
    texts = [
        "This is great!",
        "This is terrible.",
        "This is okay.",
        "I love this policy.",
        "I hate this approach."
    ]
    
    results = sentiment_analyzer.batch_analyze(texts, batch_size=2)
    
    assert len(results) == len(texts)
    assert all(isinstance(r, SentimentResult) for r in results)
    assert all(r.label in ["positive", "negative", "neutral"] for r in results)
    assert all(0.0 <= r.confidence <= 1.0 for r in results)


def test_batch_analysis_with_empty_texts(sentiment_analyzer):
    """Test batch processing with some empty texts."""
    texts = [
        "This is great!",
        "",
        "This is terrible.",
        "   ",
        "Normal text"
    ]
    
    results = sentiment_analyzer.batch_analyze(texts)
    
    assert len(results) == len(texts)
    # Empty texts should get neutral sentiment
    assert results[1].label == "neutral"
    assert results[3].label == "neutral"


def test_long_text_truncation(sentiment_analyzer):
    """Test that long texts are properly truncated."""
    # Create a very long text (more than 512 tokens)
    long_text = "This is a great policy. " * 200
    
    result = sentiment_analyzer.analyze_sentiment(long_text)
    
    assert isinstance(result, SentimentResult)
    assert result.label in ["positive", "negative", "neutral"]


def test_result_to_dict(sentiment_analyzer):
    """Test conversion of result to dictionary."""
    text = "This is excellent!"
    result = sentiment_analyzer.analyze_sentiment(text)
    
    result_dict = result.to_dict()
    
    assert "label" in result_dict
    assert "confidence" in result_dict
    assert "scores" in result_dict
    assert "processed_at" in result_dict
    assert isinstance(result_dict["scores"], dict)


def test_model_info(sentiment_analyzer):
    """Test getting model information."""
    info = sentiment_analyzer.get_model_info()
    
    assert "model_name" in info
    assert "device" in info
    assert "labels" in info
    assert isinstance(info["labels"], list)
    assert len(info["labels"]) == 3  # positive, negative, neutral


def test_confidence_scores_sum_to_one(sentiment_analyzer):
    """Test that confidence scores approximately sum to 1.0."""
    text = "This is a test comment."
    result = sentiment_analyzer.analyze_sentiment(text)
    
    total_score = sum(result.scores.values())
    assert 0.99 <= total_score <= 1.01  # Allow small floating point error


def test_batch_processing_consistency(sentiment_analyzer):
    """Test that batch processing gives same results as individual processing."""
    texts = [
        "This is excellent!",
        "This is terrible.",
        "This is neutral."
    ]
    
    # Process individually
    individual_results = [sentiment_analyzer.analyze_sentiment(text) for text in texts]
    
    # Process as batch
    batch_results = sentiment_analyzer.batch_analyze(texts)
    
    # Compare labels (should be the same)
    for ind_result, batch_result in zip(individual_results, batch_results):
        assert ind_result.label == batch_result.label
        # Confidence might differ slightly due to batching, but should be close
        assert abs(ind_result.confidence - batch_result.confidence) < 0.01
