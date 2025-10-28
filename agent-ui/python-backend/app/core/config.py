"""
Configuration management for the Python backend
"""

import os
from enum import Enum
from typing import List
from pydantic_settings import BaseSettings


class SecurityLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Settings(BaseSettings):
    """Application settings"""
    
    # Server Configuration
    PORT: int = 8003
    HOST: str = "0.0.0.0"
    
    # CORS Configuration
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:3001"
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    # Security Configuration
    DEFAULT_SECURITY_LEVEL: str = "medium"
    
    # Model Configuration
    MODEL_CACHE_DIR: str = "./models"
    USE_GPU: str = "auto"
    
    # Google Gemini Configuration
    # GEMINI_API_KEY: str = "AIzaSyAXb53gpRi_oGlX72db29tv7aMZApFtr40"  # Add your Gemini API key here or in .env
    GEMINI_API_KEY: str = "AIzaSyDduCyH7q7QiDzgPKjlda7LsufLqsGJqAA"  # Add your Gemini API key here or in .env
    GEMINI_MODEL: str = "gemini-2.5-flash"  # Gemini 2.5 Flash (1.5-flash discontinued)
    GEMINI_API_URL: str = "https://generativelanguage.googleapis.com/v1beta/models"
    
    class Config:
        env_file = ".env"
        case_sensitive = True
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins from comma-separated string"""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
    
    @property
    def security_level(self) -> SecurityLevel:
        """Get security level as enum"""
        return SecurityLevel(self.DEFAULT_SECURITY_LEVEL.lower())


# Global settings instance
settings = Settings()
