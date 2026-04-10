#!/usr/bin/env python3
"""
Minimal test to verify core project structure without external dependencies.
"""

import sys
import os
from pathlib import Path

def test_minimal():
    """Test minimal functionality."""
    
    # Add the app directory to Python path
    app_path = Path(__file__).parent / "app"
    sys.path.insert(0, str(app_path))
    
    try:
        # Test configuration
        from core.config import Settings
        settings = Settings()
        assert settings.algorithm == "HS256"
        assert settings.environment == "development"
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
        assert len(id1) == 24  # Should be 24 characters
        print("✅ ID generation works")
        
        # Test exceptions
        from core.exceptions import MCA21Exception
        try:
            raise MCA21Exception("Test exception")
        except MCA21Exception as e:
            assert str(e) == "Test exception"
        print("✅ Custom exceptions work")
        
        # Test file structure exists
        required_files = [
            "README.md",
            "requirements.txt",
            "Dockerfile",
            "docker-compose.yml",
            "app/main.py",
            "app/core/config.py",
            "app/core/database.py",
            "app/core/security.py",
            "app/models/user.py",
            "app/models/comment.py",
            "app/models/analysis.py",
            "app/api/v1/api.py",
        ]
        
        project_root = Path(__file__).parent
        missing_files = []
        for file_path in required_files:
            full_path = project_root / file_path
            if not full_path.exists():
                missing_files.append(file_path)
        
        if missing_files:
            print(f"❌ Missing files: {missing_files}")
            return False
        
        print("✅ All required files exist")
        
        print("\n🎉 All minimal tests passed! Core structure is working.")
        print("📝 Note: Full functionality requires installing dependencies with:")
        print("   pip install -r requirements.txt")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("🧪 Testing MCA21 Sentiment Analysis - Minimal Structure")
    print("=" * 60)
    success = test_minimal()
    print("=" * 60)
    sys.exit(0 if success else 1)