"""
Tests for the main FastAPI application.
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_root_endpoint(client: AsyncClient):
    """Test the root endpoint."""
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "MCA21 Sentiment Analysis System API"
    assert data["version"] == "1.0.0"


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    """Test the health check endpoint."""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["version"] == "1.0.0"


@pytest.mark.asyncio
async def test_api_v1_info(client: AsyncClient):
    """Test the API v1 info endpoint."""
    response = await client.get("/api/v1/")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "MCA21 Sentiment Analysis System API v1"
    assert "endpoints" in data