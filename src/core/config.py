"""
Application Configuration
SCRUM-20: Configure Redis caching layer
"""

from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database
    DATABASE_URL: str = "postgresql://postgres:password@localhost:5432/daily_tribune"
    
    # Redis - SCRUM-20
    REDIS_URL: str = "redis://localhost:6379"
    CACHE_TTL: int = 300  # 5 minutes
    
    # JWT Authentication - SCRUM-11
    SECRET_KEY: str = "your-secret-key-here"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # CORS
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "https://dailytribune.com"]
    
    # Elasticsearch - SCRUM-21
    ELASTICSEARCH_URL: str = "http://localhost:9200"
    
    # Rate Limiting - SCRUM-22
    RATE_LIMIT_AUTHENTICATED: int = 100  # requests per minute
    RATE_LIMIT_ANONYMOUS: int = 20
    
    class Config:
        env_file = ".env"


settings = Settings()
