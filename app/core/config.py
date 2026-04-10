"""
Configuration settings for the MCA21 Sentiment Analysis System.
"""
import os
from typing import Optional
from pydantic import BaseModel, validator


class Settings(BaseModel):
    """Application settings loaded from environment variables."""
    
    # Database Configuration
    mongodb_url: str = "mongodb://localhost:27017"
    database_name: str = "mca21_sentiment_analysis"
    
    # Redis Configuration
    redis_url: str = "redis://localhost:6379"
    
    # JWT Configuration
    secret_key: str = "your-secret-key-change-in-production-this-is-a-very-long-secret-key-for-testing"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # AI Model Configuration
    sentiment_model: str = "roberta-base"
    summarization_model: str = "t5-base"
    max_batch_size: int = 32
    
    # File Upload Configuration
    max_file_size: str = "50MB"
    upload_dir: str = "uploads/"
    
    # Logging Configuration
    log_level: str = "INFO"
    log_file: str = "logs/app.log"
    
    # Environment
    environment: str = "development"
    
    def __init__(self, **kwargs):
        # Load from environment variables
        env_values = {}
        for field_name in self.__fields__:
            env_name = field_name.upper()
            env_value = os.getenv(env_name)
            if env_value is not None:
                env_values[field_name] = env_value
        
        # Merge with provided kwargs
        env_values.update(kwargs)
        super().__init__(**env_values)
    
    @validator("secret_key")
    def validate_secret_key(cls, v):
        if len(v) < 32:
            raise ValueError("Secret key must be at least 32 characters long")
        return v
    
    @validator("max_file_size")
    def parse_file_size(cls, v):
        """Convert file size string to bytes."""
        if isinstance(v, str):
            v = v.upper()
            if v.endswith("MB"):
                return int(v[:-2]) * 1024 * 1024
            elif v.endswith("KB"):
                return int(v[:-2]) * 1024
            elif v.endswith("GB"):
                return int(v[:-2]) * 1024 * 1024 * 1024
        return int(v)


# Global settings instance
settings = Settings()