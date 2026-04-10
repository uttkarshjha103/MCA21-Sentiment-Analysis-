"""
Test authentication endpoint directly.
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from app.models.user import UserCreate, User
from app.core.security import get_password_hash
from datetime import datetime

async def test_user_creation():
    """Test user creation in database."""
    # Connect to MongoDB
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client["mca21_sentiment_analysis"]
    
    try:
        # Create user data
        user_data = UserCreate(
            name="Test User",
            email="test@example.com",
            password="TestPassword123!",
            role="analyst"
        )
        
        print(f"✓ UserCreate model created: {user_data.name}")
        
        # Create user document for database
        user_doc = {
            "name": user_data.name,
            "email": user_data.email,
            "password_hash": get_password_hash(user_data.password),
            "role": user_data.role,
            "created_at": datetime.utcnow(),
            "is_active": True,
            "failed_login_attempts": 0,
            "locked_until": None
        }
        
        print("✓ User document created")
        
        # Insert into database
        result = await db.users.insert_one(user_doc)
        user_doc["_id"] = result.inserted_id
        
        print(f"✓ User inserted with ID: {result.inserted_id}")
        
        # Create User model from document
        user = User(**user_doc)
        print(f"✓ User model created: {user.name} ({user.email})")
        
        # Clean up
        await db.users.delete_one({"_id": result.inserted_id})
        print("✓ Test user cleaned up")
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        client.close()

if __name__ == "__main__":
    print("Testing user creation in database...")
    asyncio.run(test_user_creation())