# @track_context("config.md")

import logging
import os
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    """Application settings"""
    # Base App Config
    APP_NAME: str = "LongSorn API"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = False
    TESTING: bool = False
    LOG_LEVEL: str = "INFO"
    
    # Supabase API (for Auth)
    SUPABASE_URL: str
    SUPABASE_KEY: str
    SUPABASE_JWT_SECRET: str

    # Redis (for Job Queue)
    REDIS_URL: str
    JOB_QUEUE_NAME: str = "long-sorn"

    # Direct Database Connection (for SQLAlchemy)
    DATABASE_URL: str

    # Cloudflare R2 (for Object Storage)
    R2_ENDPOINT_URL: str
    R2_ACCESS_KEY_ID: str
    R2_SECRET_ACCESS_KEY: str
    R2_BUCKET_NAME: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding='utf-8'
    )

@lru_cache()
def get_settings():
    return Settings()

settings = get_settings()