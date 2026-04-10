#!/usr/bin/env python3
"""
Basic test without external dependencies to verify core structure.
"""

import sys
import os
from pathlib import Path

def test_basic_structure():
    """Test basic project structure and core functionality."""
    
    # Add the app directory to Python path
    app_path = Path(__file__).parent / "app"
    sys.path.insert(0, str(app_path))
    
    try:
        # Test configuration
        from core.config import Settings
        settings = Settings()
        assert settings.algorithm == "HS256"
        print("✅ Configuration works")
        
        # Test utilities
        from utils.helpers import clean_text, generate_id
        
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
        
        # Test models (basic structure)
        from models.user import UserRole
        assert UserRole.ADMIN == "admin"
        assert UserRole.ANALYST == "analyst"
        print("✅ User roles work")
        
        # Test exceptions
        from core.exceptions import MCA21Exception
        try:
            raise MCA21Exception("Test exception")
        except MCA21Exception as e:
            assert str(e) == "Test exception"
        print("✅ Custom exceptions work")
        
        print("\n🎉 All basic tests passed! Core structure is working.")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_basic_structure()
    sys.exit(0 if success else 1)