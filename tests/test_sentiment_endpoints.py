"""
Integration tests for sentiment analysis API endpoints.
Tests the sentiment analysis endpoints with authentication.
"""

import pytest
from httpx import AsyncClient
from app.main import app


@pytest.mark.asyncio
async def test_analyze_sentiment_endpoint(client, auth_headers):
    """Test single sentiment analysis endpoint."""
    response = await client.post(
        "/api/v1/sentiment/analyze",
        json={"text": "This is an excellent policy!"},
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "label" in data
    assert "confidence" in data
    assert "scores" in data
    assert data["label"] in ["positive", "negative", "neutral"]
    assert 0.0 <= data["confidence"] <= 1.0


@pytest.mark.asyncio
async def test_analyze_sentiment_without_auth(client):
    """Test sentiment analysis endpoint requires authentication."""
    response = await client.post(
        "/api/v1/sentiment/analyze",
        json={"text": "This is a test"}
    )
    
    assert response.status_code == 401  # Unauthorized, not Forbidden


@pytest.mark.asyncio
async def test_batch_sentiment_analysis(client, auth_headers):
    """Test batch sentiment analysis endpoint."""
    texts = [
        "This is great!",
        "This is terrible.",
        "This is okay."
    ]
    
    response = await client.post(
        "/api/v1/sentiment/analyze/batch",
        json={"texts": texts, "batch_size": 2},
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert "total_processed" in data
    assert "model_info" in data
    assert len(data["results"]) == len(texts)
    assert data["total_processed"] == len(texts)


@pytest.mark.asyncio
async def test_batch_sentiment_empty_list(client, auth_headers):
    """Test batch sentiment analysis with empty list."""
    response = await client.post(
        "/api/v1/sentiment/analyze/batch",
        json={"texts": []},
        headers=auth_headers
    )
    
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_get_model_info(client, auth_headers):
    """Test getting model information."""
    response = await client.get(
        "/api/v1/sentiment/model-info",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "model_name" in data
    assert "device" in data
    assert "labels" in data
    assert isinstance(data["labels"], list)
    assert len(data["labels"]) == 3


@pytest.mark.asyncio
async def test_sentiment_analysis_various_texts(client, auth_headers):
    """Test sentiment analysis with various text types."""
    test_cases = [
        ("I love this policy!", "positive"),
        ("This is terrible and I hate it.", "negative"),
        ("The document contains several sections.", None),  # Could be any
        ("", "neutral"),  # Empty text should be neutral
    ]
    
    for text, expected_label in test_cases:
        response = await client.post(
            "/api/v1/sentiment/analyze",
            json={"text": text},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        if expected_label:
            assert data["label"] == expected_label
        else:
            assert data["label"] in ["positive", "negative", "neutral"]
