"""
Pytest configuration and fixtures for testing.
"""
import asyncio
import pytest
import pytest_asyncio
import httpx
from httpx import AsyncClient
from unittest.mock import AsyncMock, MagicMock
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from bson import ObjectId

from app.main import app
from app.core.database import get_database
from app.core.config import settings


# Mock database for testing
class MockDatabase:
    def __init__(self):
        self.users = AsyncMock()
        self.comments = AsyncMock()
        self.reports = AsyncMock()
        self.audit_logs = AsyncMock()
        self.upload_progress = AsyncMock()
        
        # In-memory storage for testing
        self._users_storage = {}
        self._comments_storage = {}
        self._audit_logs_storage = []
        self._upload_progress_storage = {}
        
        # Configure mock behaviors
        self.users.find_one = AsyncMock(side_effect=self._find_user)
        self.users.insert_one = AsyncMock(side_effect=self._insert_user)
        self.users.update_one = AsyncMock(side_effect=self._update_user)
        self.users.create_index = AsyncMock()
        
        self.audit_logs.insert_one = AsyncMock(side_effect=self._insert_audit_log)
        self.audit_logs.find_one = AsyncMock(side_effect=self._find_audit_log)
        self.audit_logs.find = MagicMock(side_effect=self._find_audit_logs)
        self.audit_logs.count_documents = AsyncMock(side_effect=self._count_audit_logs)
        self.audit_logs.delete_many = AsyncMock(side_effect=self._delete_audit_logs)
        self.audit_logs.create_index = AsyncMock()
        
        self.comments.insert_one = AsyncMock(side_effect=self._insert_one_comment)
        self.comments.insert_many = AsyncMock(side_effect=self._insert_many_comments)
        self.comments.find_one = AsyncMock(side_effect=self._find_comment)
        self.comments.count_documents = AsyncMock(side_effect=self._count_comments)
        self.comments.create_index = AsyncMock()
        
        self.upload_progress.insert_one = AsyncMock(side_effect=self._insert_upload_progress)
        self.upload_progress.find_one = AsyncMock(side_effect=self._find_upload_progress)
        self.upload_progress.update_one = AsyncMock(side_effect=self._update_upload_progress)
        self.upload_progress.create_index = AsyncMock()
        
        self.reports.create_index = AsyncMock()
    
    async def _find_user(self, query):
        """Mock find_one for users collection."""
        if "email" in query:
            email = query["email"]
            return self._users_storage.get(email)
        elif "_id" in query:
            user_id = query["_id"]
            for user_data in self._users_storage.values():
                if user_data.get("_id") == user_id:
                    return user_data
        return None
    
    async def _insert_user(self, user_doc):
        """Mock insert_one for users collection."""
        from bson import ObjectId
        user_id = ObjectId()
        user_doc["_id"] = user_id
        self._users_storage[user_doc["email"]] = user_doc
        
        mock_result = MagicMock()
        mock_result.inserted_id = user_id
        return mock_result
    
    async def _update_user(self, query, update):
        """Mock update_one for users collection."""
        if "email" in query:
            email = query["email"]
            if email in self._users_storage:
                if "$set" in update:
                    self._users_storage[email].update(update["$set"])
        elif "_id" in query:
            user_id = query["_id"]
            for email, user_data in self._users_storage.items():
                if user_data.get("_id") == user_id:
                    if "$set" in update:
                        user_data.update(update["$set"])
                    break
        
        mock_result = MagicMock()
        mock_result.modified_count = 1
        return mock_result
    
    async def _insert_audit_log(self, log_doc):
        """Mock insert_one for audit_logs collection."""
        from bson import ObjectId
        log_id = ObjectId()
        log_doc["_id"] = log_id
        self._audit_logs_storage.append(log_doc)
        
        mock_result = MagicMock()
        mock_result.inserted_id = log_id
        return mock_result
    
    async def _find_audit_log(self, query):
        """Mock find_one for audit_logs collection."""
        for log in self._audit_logs_storage:
            match = True
            for key, value in query.items():
                if log.get(key) != value:
                    match = False
                    break
            if match:
                return log
        return None
    
    def _find_audit_logs(self, query=None):
        """Mock find for audit_logs collection."""
        query = query or {}
        
        class MockCursor:
            def __init__(self, logs, query):
                self.logs = logs
                self.query = query
                self._skip = 0
                self._limit = None
                self._sort_field = None
                self._sort_order = 1
            
            def sort(self, field, order=1):
                self._sort_field = field
                self._sort_order = order
                return self
            
            def skip(self, count):
                self._skip = count
                return self
            
            def limit(self, count):
                self._limit = count
                return self
            
            async def __aiter__(self):
                # Filter logs
                filtered = []
                for log in self.logs:
                    match = True
                    for key, value in self.query.items():
                        if log.get(key) != value:
                            match = False
                            break
                    if match:
                        filtered.append(log)
                
                # Sort if needed
                if self._sort_field:
                    filtered.sort(key=lambda x: x.get(self._sort_field, ""), reverse=(self._sort_order == -1))
                
                # Apply skip and limit
                filtered = filtered[self._skip:]
                if self._limit:
                    filtered = filtered[:self._limit]
                
                for log in filtered:
                    yield log
        
        return MockCursor(self._audit_logs_storage, query)
    
    async def _count_audit_logs(self, query):
        """Mock count_documents for audit_logs collection."""
        count = 0
        for log in self._audit_logs_storage:
            match = True
            for key, value in query.items():
                if log.get(key) != value:
                    match = False
                    break
            if match:
                count += 1
        return count
    
    async def _delete_audit_logs(self, query):
        """Mock delete_many for audit_logs collection."""
        to_remove = []
        for log in self._audit_logs_storage:
            match = True
            for key, value in query.items():
                if log.get(key) != value:
                    match = False
                    break
            if match:
                to_remove.append(log)
        
        for log in to_remove:
            self._audit_logs_storage.remove(log)
        
        mock_result = MagicMock()
        mock_result.deleted_count = len(to_remove)
        return mock_result
    
    def clear_storage(self):
        """Clear all stored data."""
        self._users_storage.clear()
        self._comments_storage.clear()
        self._audit_logs_storage.clear()
        self._upload_progress_storage.clear()
    
    async def _insert_one_comment(self, document):
        """Mock insert_one for comments collection."""
        from bson import ObjectId
        comment_id = ObjectId()
        document["_id"] = comment_id
        self._comments_storage[str(comment_id)] = document
        
        mock_result = MagicMock()
        mock_result.inserted_id = comment_id
        return mock_result
    
    async def _insert_many_comments(self, documents, ordered=True):
        """Mock insert_many for comments collection."""
        from bson import ObjectId
        inserted_ids = []
        for doc in documents:
            comment_id = ObjectId()
            doc["_id"] = comment_id
            self._comments_storage[str(comment_id)] = doc
            inserted_ids.append(comment_id)
        
        mock_result = MagicMock()
        mock_result.inserted_ids = inserted_ids
        return mock_result
    
    async def _find_comment(self, query):
        """Mock find_one for comments collection."""
        if "_id" in query:
            comment_id = str(query["_id"])
            return self._comments_storage.get(comment_id)
        return None
    
    async def _count_comments(self, query):
        """Mock count_documents for comments collection."""
        return len(self._comments_storage)
    
    async def _insert_upload_progress(self, progress_doc):
        """Mock insert_one for upload_progress collection."""
        from bson import ObjectId
        progress_id = ObjectId()
        progress_doc["_id"] = progress_id
        upload_id = progress_doc["upload_id"]
        self._upload_progress_storage[upload_id] = progress_doc
        
        mock_result = MagicMock()
        mock_result.inserted_id = progress_id
        return mock_result
    
    async def _find_upload_progress(self, query):
        """Mock find_one for upload_progress collection."""
        if "upload_id" in query:
            upload_id = query["upload_id"]
            return self._upload_progress_storage.get(upload_id)
        return None
    
    async def _update_upload_progress(self, query, update):
        """Mock update_one for upload_progress collection."""
        if "upload_id" in query:
            upload_id = query["upload_id"]
            if upload_id in self._upload_progress_storage:
                if "$set" in update:
                    self._upload_progress_storage[upload_id].update(update["$set"])
        
        mock_result = MagicMock()
        mock_result.modified_count = 1
        return mock_result


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def mock_db():
    """Create a mock database for testing."""
    db = MockDatabase()
    yield db
    db.clear_storage()


@pytest_asyncio.fixture
async def test_db():
    """Create a real test database connection."""
    # Use a test database
    client = AsyncIOMotorClient(settings.mongodb_url)
    db = client["mca21_test"]
    
    yield db
    
    # Clean up test data
    await db.users.delete_many({})
    await db.audit_logs.delete_many({})
    await db.comments.delete_many({})
    client.close()


@pytest_asyncio.fixture
async def client(mock_db):
    """Create a test client with mock database."""
    # Override the database dependency
    app.dependency_overrides[get_database] = lambda: mock_db
    
    async with AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    
    # Clean up
    app.dependency_overrides.clear()
    mock_db.clear_storage()


@pytest_asyncio.fixture
async def async_client(test_db):
    """Create a test client with real test database."""
    # Override the database dependency
    app.dependency_overrides[get_database] = lambda: test_db
    
    async with AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    
    # Clean up
    app.dependency_overrides.clear()


@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        "name": "Test User",
        "email": "test@example.com",
        "password": "TestPassword123!",
        "role": "analyst"
    }


@pytest.fixture
def sample_comment_data():
    """Sample comment data for testing."""
    return {
        "comment_text": "This is a test comment for sentiment analysis.",
        "source": "test_source",
        "metadata": {"test": True}
    }


@pytest.fixture
def sample_comments_batch():
    """Sample batch of comments for testing."""
    return [
        {
            "comment_text": "This policy is excellent and well thought out.",
            "source": "public_consultation_2024"
        },
        {
            "comment_text": "I disagree with the proposed changes.",
            "source": "public_consultation_2024"
        },
        {
            "comment_text": "The implementation timeline seems reasonable.",
            "source": "public_consultation_2024"
        }
    ]


@pytest_asyncio.fixture
async def auth_headers(client):
    """Create authentication headers with a valid token."""
    # Register a test user
    user_data = {
        "name": "Test User",
        "email": "test@example.com",
        "password": "TestPassword123!",
        "role": "analyst"
    }
    
    response = await client.post("/api/v1/auth/register", json=user_data)
    assert response.status_code == 201
    
    data = response.json()
    token = data["access_token"]
    
    return {"Authorization": f"Bearer {token}"}
