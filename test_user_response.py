"""
Test UserResponse creation specifically.
"""
from app.models.user import User, UserResponse
from datetime import datetime
from bson import ObjectId

def test_user_response_creation():
    """Test creating UserResponse from User."""
    # Create a User object (simulating what comes from database)
    user_doc = {
        "_id": ObjectId(),
        "name": "Test User",
        "email": "test@example.com",
        "password_hash": "hashed_password",
        "role": "analyst",
        "created_at": datetime.utcnow(),
        "is_active": True,
        "failed_login_attempts": 0,
        "locked_until": None,
        "last_login": None
    }
    
    user = User(**user_doc)
    print(f"✓ User created: {user.name}")
    print(f"  User ID: {user.id}")
    print(f"  User ID type: {type(user.id)}")
    
    # Create UserResponse (this is where the error might be)
    try:
        user_response = UserResponse(
            _id=str(user.id),
            name=user.name,
            email=user.email,
            role=user.role,
            created_at=user.created_at,
            last_login=user.last_login,
            is_active=user.is_active
        )
        print(f"✓ UserResponse created: {user_response.name}")
        print(f"  Response ID: {user_response.id}")
        print(f"  Response ID type: {type(user_response.id)}")
        
    except Exception as e:
        print(f"✗ Error creating UserResponse: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("Testing UserResponse creation...")
    test_user_response_creation()