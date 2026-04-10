"""
Integration tests for upload endpoints.
"""
import pytest
from io import BytesIO
import httpx
from httpx import AsyncClient
from app.main import app
from app.core.database import get_database
from openpyxl import Workbook


@pytest.mark.asyncio
async def test_upload_csv_endpoint_unauthorized(mock_db):
    """Test CSV upload endpoint without authentication."""
    app.dependency_overrides[get_database] = lambda: mock_db
    
    async with AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        csv_content = b"comment_text,source\nTest comment,test"
        files = {"file": ("test.csv", BytesIO(csv_content), "text/csv")}
        
        response = await client.post("/api/v1/upload/csv", files=files)
        
        assert response.status_code == 401
    
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_upload_excel_endpoint_unauthorized(mock_db):
    """Test Excel upload endpoint without authentication."""
    app.dependency_overrides[get_database] = lambda: mock_db
    
    async with AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        wb = Workbook()
        ws = wb.active
        ws.append(["comment_text", "source"])
        ws.append(["Test comment", "test"])
        
        excel_buffer = BytesIO()
        wb.save(excel_buffer)
        excel_buffer.seek(0)
        
        files = {"file": ("test.xlsx", excel_buffer, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        
        response = await client.post("/api/v1/upload/excel", files=files)
        
        assert response.status_code == 401
    
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_upload_csv_invalid_extension(mock_db):
    """Test CSV upload with invalid file extension."""
    app.dependency_overrides[get_database] = lambda: mock_db
    
    # First register and login to get token
    async with AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        # Register user
        register_data = {
            "name": "Test User",
            "email": "test_csv_ext@example.com",
            "password": "TestPass123!",
            "role": "analyst"
        }
        register_response = await client.post("/api/v1/auth/register", json=register_data)
        assert register_response.status_code == 201
        
        token = register_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Try to upload file with wrong extension
        csv_content = b"comment_text,source\nTest comment,test"
        files = {"file": ("test.pdf", BytesIO(csv_content), "application/pdf")}
        
        response = await client.post("/api/v1/upload/csv", files=files, headers=headers)
        
        assert response.status_code == 400
        assert "Invalid file extension" in response.json()["detail"]
    
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_upload_excel_invalid_extension(mock_db):
    """Test Excel upload with invalid file extension."""
    app.dependency_overrides[get_database] = lambda: mock_db
    
    # First register and login to get token
    async with AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        # Register user
        register_data = {
            "name": "Test User",
            "email": "test_excel_ext@example.com",
            "password": "TestPass123!",
            "role": "analyst"
        }
        register_response = await client.post("/api/v1/auth/register", json=register_data)
        assert register_response.status_code == 201
        
        token = register_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Try to upload file with wrong extension
        csv_content = b"comment_text,source\nTest comment,test"
        files = {"file": ("test.csv", BytesIO(csv_content), "text/csv")}
        
        response = await client.post("/api/v1/upload/excel", files=files, headers=headers)
        
        assert response.status_code == 400
        assert "Invalid file extension" in response.json()["detail"]
    
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_manual_comment_upload(mock_db):
    """Test manual comment upload endpoint."""
    app.dependency_overrides[get_database] = lambda: mock_db
    
    async with AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        # Register user
        register_data = {
            "name": "Test User",
            "email": "test_manual@example.com",
            "password": "TestPass123!",
            "role": "analyst"
        }
        register_response = await client.post("/api/v1/auth/register", json=register_data)
        assert register_response.status_code == 201
        
        token = register_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Upload manual comment
        comment_data = {
            "comment_text": "This is a manually entered comment",
            "source": "manual_entry",
            "original_language": "en"
        }
        
        response = await client.post("/api/v1/upload/manual", json=comment_data, headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["comment_text"] == "This is a manually entered comment"
        assert data["source"] == "manual_entry"
        assert "_id" in data
    
    app.dependency_overrides.clear()
