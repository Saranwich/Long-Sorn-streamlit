# @track_context("config.md")

import logging
import os

from pydantic_settings import BaseSettings, SettingsConfigDict

from src.core.constants import Defaults, EnvVars
from src.core.secrets import load_secrets_from_gsm, should_use_gsm

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Application settings"""

    # Base
    APP_NAME: str = Defaults.APP_NAME
    API_V1_STR: str = Defaults.API_V1_STR

    # App metadata
    APP_VERSION: str = Defaults.APP_VERSION
    APP_DESCRIPTION: str = Defaults.APP_DESCRIPTION

    # CORS settings
    CORS_ORIGINS: list[str] = Defaults.CORS_ORIGINS

    # Supabase - make these optional with defaults
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""
    SUPABASE_JWT_SECRET: str = ""

    # Application settings
    DEBUG: bool = Defaults.DEBUG
    TESTING: bool = Defaults.TESTING
    LOG_LEVEL: str = Defaults.LOG_LEVEL
    USE_GSM: bool = Defaults.USE_GSM

    # Redis for Job Queue
    REDIS_URL: str
    JOB_QUEUE_NAME: str = "video-processing-queue"

    model_config = SettingsConfigDict(env_file=".env")


def get_settings() -> Settings:
    """Get application settings with optional Google Secret Manager integration"""
    # Load secrets from GSM if enabled (automatically falls back to env variables)
    if should_use_gsm():
        load_secrets_from_gsm()

    return Settings()


def should_use_testing() -> bool:
    return os.environ.get(EnvVars.TESTING, "").lower() in ("true", "1", "t")


# Load settings using the function
settings = get_settings()

# Set log level
LOG_LEVEL = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)