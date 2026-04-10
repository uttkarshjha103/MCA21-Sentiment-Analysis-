"""
Simple test to verify authentication functionality works.
"""
import asyncio
from app.core.security import get_password_hash, verify_password, create_access_token, verify_token, validate_password_strength
from app.models.user import UserCreate, UserRole


def test_password_hashing():
    """Test password hashing and verification."""
    password = "TestPassword123!"
    hashed = get_password_hash(password)
    
    # Verify correct password
    assert verify_password(password, hashed) is True
    
    # Verify incorrect password
    assert verify_password("WrongPassword", hashed) is False
    
    print("✓ Password hashing and verification works")


def test_jwt_tokens():
    """Test JWT token creation and verification."""
    data = {"sub": "test@example.com", "role": "analyst"}
    token = create_access_token(data)
    
    # Verify token
    payload = verify_token(token)
    assert payload is not None
    assert payload["sub"] == "test@example.com"
    assert payload["role"] == "analyst"
    
    # Verify invalid token
    invalid_payload = verify_token("invalid_token")
    assert invalid_payload is None
    
    print("✓ JWT token creation and verification works")


def test_password_validation():
    """Test password strength validation."""
    # Valid password
    is_valid, message = validate_password_strength("ValidPassword123!")
    assert is_valid is True
    assert message == "Password is valid"
    
    # Invalid passwords
    test_cases = [
        ("short", "Password must be at least 8 characters long"),
        ("nouppercase123!", "Password must contain at least one uppercase letter"),
        ("NOLOWERCASE123!", "Password must contain at least one lowercase letter"),
        ("NoDigits!", "Password must contain at least one digit"),
        ("NoSpecialChars123", "Password must contain at least one special character"),
    ]
    
    for password, expected_error in test_cases:
        is_valid, message = validate_password_strength(password)
        assert is_valid is False
        assert expected_error in message
    
    print("✓ Password validation works")


def test_user_models():
    """Test user model creation."""
    # Test UserCreate model
    user_data = {
        "name": "Test User",
        "email": "test@example.com",
        "password": "TestPassword123!",
        "role": UserRole.ANALYST
    }
    
    user_create = UserCreate(**user_data)
    assert user_create.name == "Test User"
    assert user_create.email == "test@example.com"
    assert user_create.role == UserRole.ANALYST
    
    print("✓ User models work")


if __name__ == "__main__":
    print("Testing authentication components...")
    
    test_password_hashing()
    test_jwt_tokens()
    test_password_validation()
    test_user_models()
    
    print("\n✅ All authentication tests passed!")