"""Configuration management for the application."""

import os
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    
    # Server settings
    host: str = "0.0.0.0"
    port: int = 5000
    debug: bool = True
    
    # CORS settings
    allowed_origins: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://jite.vercel.app",
    ]
    
    # Supabase settings
    supabase_url: str = ""
    supabase_key: str = ""
    
    # Alternative naming for environment variables
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""
    
    # API settings
    api_prefix: str = "/api"
    title: str = "SPM Backend API"
    description: str = "Backend API for SPM Frontend"
    version: str = "1.0.0"
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields in .env file


# Global settings instance
settings = Settings()
