"""
Configuration settings for the Document Intelligence Platform.

This module contains all configuration variables including paths, 
database settings, API keys, and model configurations.
"""

import os
from pathlib import Path
from typing import Optional
try:
    from pydantic_settings import BaseSettings # type: ignore
except ImportError:
    from pydantic import BaseSettings # type: ignore


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Application settings
    APP_NAME: str = "Document Intelligence Platform"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Paths
    BASE_DIR: Path = Path(__file__).parent.parent
    UPLOAD_FOLDER: Path = BASE_DIR / "data" / "uploads"
    PROCESSED_FOLDER: Path = BASE_DIR / "data" / "processed"
    SAMPLE_FOLDER: Path = BASE_DIR / "data" / "sample"
    
    # Database
    DATABASE_URL: str = "sqlite:///./document_intelligence.db"
    
    # Security
    JWT_SECRET_KEY: str = "your-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS
    CORS_ORIGINS: list = ["http://localhost:3000", "http://127.0.0.1:3000"]
    
    # Model Paths and Settings
    OCR_MODEL_PATH: Optional[str] = None
    SUMMARIZATION_MODEL: str = "facebook/bart-large-cnn"
    NER_MODEL: str = "dbmdz/bert-large-cased-finetuned-conll03-english"
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    CLASSIFICATION_MODEL: str = "distilbert-base-uncased"
    
    # API Keys and External Services
    OPENAI_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    
    # Gemini Configuration
    GEMINI_MODEL: str = "gemini-2.5-flash"
    GEMINI_TEMPERATURE: float = 0.1
    GEMINI_MAX_TOKENS: int = 8192
    
    # Enhanced Features
    ENABLE_GEMINI_CHAT: bool = True
    ENABLE_GEMINI_ANALYSIS: bool = True
    
    # Search Settings
    FAISS_INDEX_PATH: Path = BASE_DIR / "data" / "processed" / "faiss_index"
    MAX_SEARCH_RESULTS: int = 10
    
    # File Upload Settings
    MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50MB
    ALLOWED_EXTENSIONS: set = {".pdf", ".txt", ".docx", ".png", ".jpg", ".jpeg"}
    
    # API Settings
    API_V1_PREFIX: str = "/api/v1"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()

# Ensure directories exist
settings.UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
settings.PROCESSED_FOLDER.mkdir(parents=True, exist_ok=True)
settings.SAMPLE_FOLDER.mkdir(parents=True, exist_ok=True)