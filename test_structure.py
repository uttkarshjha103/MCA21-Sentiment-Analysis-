#!/usr/bin/env python3
"""
Simple test to verify the project structure is correct.
This test doesn't require external dependencies.
"""

import sys
import os
from pathlib import Path

def test_project_structure():
    """Test that all required files and directories exist."""
    
    # Get the project root directory
    project_root = Path(__file__).parent
    
    # Required files
    required_files = [
        "README.md",
        "requirements.txt",
        ".env.example",
        "Dockerfile",
        "docker-compose.yml",
        ".gitignore",
        "app/__init__.py",
        "app/main.py",
        "app/core/__init__.py",
        "app/core/config.py",
        "app/core/database.py",
        "app/core/security.py",
        "app/core/logging.py",
        "app/core/exceptions.py",
        "app/core/middleware.py",
        "app/models/__init__.py",
        "app/models/user.py",
        "app/models/comment.py",
        "app/models/analysis.py",
        "app/api/__init__.py",
        "app/api/v1/__init__.py",
        "app/api/v1/api.py",
        "app/services/__init__.py",
        "app/utils/__init__.py",
        "app/utils/helpers.py",
        "tests/__init__.py",
        "tests/conftest.py",
        "tests/test_main.py",
    ]
    
    missing_files = []
    for file_path in required_files:
        full_path = project_root / file_path
        if not full_path.exists():
            missing_files.append(file_path)
    
    if missing_files:
        print(f"❌ Missing files: {missing_files}")
        return False
    
    print("✅ All required files exist")
    return True


def test_imports():
    """Test that basic imports work."""
    try:
        # Add the app directory to Python path
        app_path = Path(__file__).parent / "app"
        sys.path.insert(0, str(app_path))
        
        # Test core imports
        from core.config import Settings
        from core.exceptions import MCA21Exception
        from core.security import get_password_hash, verify_password
        
        # Test model imports
        from models.user import User, UserCreate, UserRole
        from models.comment import Comment, CommentCreate
        from models.analysis import SentimentResult, Keyword
        
        # Test utility imports
        from utils.helpers import clean_text, generate_id
        
        print("✅ All imports successful")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


def test_basic_functionality():
    """Test basic functionality without external dependencies."""
    try:
        # Add the app directory to Python path
        app_path = Path(__file__).parent / "app"
        sys.path.insert(0, str(app_path))
        
        from core.config import Settings
        from core.security import get_password_hash, verify_password
        from utils.helpers import clean_text, generate_id
        from models.user import UserRole
        
        # Test configuration
        settings = Settings()
        assert settings.algorithm == "HS256"
        print("✅ Configuration works")
        
        # Test password hashing
        password = "TestPassword123!"
        hashed = get_password_hash(password)
        assert verify_password(password, hashed)
        assert not verify_password("wrong_password", hashed)
        print("✅ Password hashing works")
        
        # Test text cleaning
        dirty_text = "  This is   a test   with   extra   spaces  "
        clean = clean_text(dirty_text)
        assert clean == "This is a test with extra spaces"
        print("✅ Text cleaning works")
        
        # Test ID generation
        id1 = generate_id()
        id2 = generate_id()
        assert id1 != id2
        assert len(id1) == 24  # ObjectId length
        print("✅ ID generation works")
        
        # Test enum
        assert UserRole.ADMIN == "admin"
        assert UserRole.ANALYST == "analyst"
        print("✅ User roles work")
        
        return True
        
    except Exception as e:
        print(f"❌ Functionality test error: {e}")
        return False


def main():
    """Run all tests."""
    print("🧪 Testing MCA21 Sentiment Analysis Project Structure")
    print("=" * 60)
    
    tests = [
        ("Project Structure", test_project_structure),
        ("Module Imports", test_imports),
        ("Basic Functionality", test_basic_functionality),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 Running: {test_name}")
        if test_func():
            passed += 1
        else:
            print(f"❌ {test_name} failed")
    
    print("\n" + "=" * 60)
    print(f"📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Project structure is correct.")
        return True
    else:
        print("❌ Some tests failed. Please check the issues above.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)