"""
Test user model creation directly.
"""
from app.models.user import User, UserCreate, UserResponse
from datetime import datetime
from bson import ObjectId

def test_user_create():
    """Test UserCreate model."""
    user_data = {
        "name": "Test User",
        "email": "test@example.com",
        "password": "TestPassword123!",
        "role": "analyst"
    }
    
    user_create = UserCreate(**user_data)
    print(f"✓ UserCreate: {user_create.name} ({user_create.email})")

def test_user_model():
    """Test User model."""
    user_data = {
        "name": "Test User",
        "email": "test@example.com",
        "password_hash": "hashed_password",
        "role": "analyst",
        "created_at": datetime.utcnow(),
        "is_active": True,
        "failed_login_attempts": 0,
        "locked_until": None
    }
    
    user = User(**user_data)
    print(f"✓ User: {user.name} ({user.email})")

def test_user_response():
    """Test UserResponse model."""
    user_data = {
        "_id": str(ObjectId()),
        "name": "Test User",
        "email": "test@example.com",
        "role": "analyst",
        "created_at": datetime.utcnow(),
        "is_active": True
    }
    
    user_response = UserResponse(**user_data)
    print(f"✓ UserResponse: {user_response.name} ({user_response.email})")

if __name__ == "__main__":
    print("Testing user models...")
    
    test_user_create()
    test_user_model()
    test_user_response()
    
    print("\n✅ All user model tests passed!")