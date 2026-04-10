"""
Test the full registration flow step by step.
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from app.models.user import UserCreate, User, UserResponse, TokenResponse
from app.core.security import get_password_hash, create_access_token, validate_password_strength
from datetime import datetime, timedelta

async def test_full_registration():
    """Test the complete registration flow."""
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client["mca21_sentiment_analysis"]
    
    try:
        print("1. Creating UserCreate model...")
        user_data = UserCreate(
            name="Test User",
            email="test2@example.com",
            password="TestPassword123!",
            role="analyst"
        )
        print(f"✓ UserCreate: {user_data.name}")
        
        print("\n2. Validating password...")
        is_valid, error_message = validate_password_strength(user_data.password)
        if not is_valid:
            print(f"✗ Password validation failed: {error_message}")
            return
        print("✓ Password validation passed")
        
        print("\n3. Creating user document...")
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
        
        print("\n4. Inserting into database...")
        result = await db.users.insert_one(user_doc)
        user_doc["_id"] = result.inserted_id
        print(f"✓ User inserted with ID: {result.inserted_id}")
        
        print("\n5. Creating User model...")
        user = User(**user_doc)
        print(f"✓ User model: {user.name} (ID: {user.id})")
        
        print("\n6. Creating access token...")
        access_token_expires = timedelta(minutes=30)
        access_token = create_access_token(
            data={"sub": user.email, "role": user.role},
            expires_delta=access_token_expires
        )
        print("✓ Access token created")
        
        print("\n7. Creating UserResponse...")
        user_response = UserResponse(
            _id=str(user.id),
            name=user.name,
            email=user.email,
            role=user.role,
            created_at=user.created_at,
            last_login=user.last_login,
            is_active=user.is_active
        )
        print(f"✓ UserResponse: {user_response.name}")
        
        print("\n8. Creating TokenResponse...")
        token_response = TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=1800,
            user=user_response
        )
        print("✓ TokenResponse created")
        
        print("\n9. Converting to dict (simulating JSON response)...")
        response_dict = token_response.model_dump()
        print(f"✓ Response dict created with keys: {list(response_dict.keys())}")
        
        # Clean up
        await db.users.delete_one({"_id": result.inserted_id})
        print("\n✓ Test user cleaned up")
        
        print("\n✅ Full registration flow completed successfully!")
        
    except Exception as e:
        print(f"\n✗ Error in registration flow: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        client.close()

if __name__ == "__main__":
    print("Testing full registration flow...")
    asyncio.run(test_full_registration())