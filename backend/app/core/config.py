import os
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    PROJECT_NAME: str = "CyberVerify"
    VERSION: str = "1.0.0"
    API_PREFIX: str = "/api"
    
    # MongoDB
    MONGODB_URL: str = Field(default="mongodb://localhost:27017", alias="MONGODB_URL")
    DATABASE_NAME: str = Field(default="cyberverify_db", alias="DATABASE_NAME")
    
    # AI & Search APIs
    TAVILY_API_KEY: Optional[str] = Field(default=None, alias="TAVILY_API_KEY")
    GEMINI_API_KEY: Optional[str] = Field(default=None, alias="GEMINI_API_KEY")
    OPENAI_API_KEY: Optional[str] = Field(default=None, alias="OPENAI_API_KEY")
    OPENAI_BASE_URL: Optional[str] = Field(default=None, alias="OPENAI_BASE_URL")
    
    # Security & Scraping
    REQUEST_TIMEOUT: int = Field(default=15, alias="REQUEST_TIMEOUT")
    MAX_SEARCH_RESULTS: int = Field(default=10, alias="MAX_SEARCH_RESULTS")
    RATE_LIMIT_PER_MINUTE: int = Field(default=60, alias="RATE_LIMIT_PER_MINUTE")
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "*"
    ]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

settings = Settings()
