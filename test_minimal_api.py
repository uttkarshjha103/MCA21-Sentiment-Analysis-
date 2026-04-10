"""
Minimal FastAPI test for authentication.
"""
from fastapi import FastAPI, HTTPException, status
from app.models.user import UserCreate, TokenResponse, UserResponse
from app.core.security import get_password_hash, create_access_token
from datetime import datetime, timedelta
import uvicorn

app = FastAPI()

@app.post("/test-register", response_model=TokenResponse)
async def test_register(user_data: UserCreate):
    """Test registration endpoint."""
    try:
        # Simulate user creation
        user_response = UserResponse(
            _id="507f1f77bcf86cd799439011",  # Mock ObjectId string
            name=user_data.name,
            email=user_data.email,
            role=user_data.role,
            created_at=datetime.utcnow(),
            is_active=True
        )
        
        # Create token
        access_token = create_access_token(
            data={"sub": user_data.email, "role": user_data.role},
            expires_delta=timedelta(minutes=30)
        )
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=1800,
            user=user_response
        )
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)