# @track_context("core_constants.md")

"""
Core constants for the Supabase Auth API

This module contains essential configuration constants that are used
across multiple modules in the application.
"""


class EnvVars:
    """Environment variable names"""

    # Core settings
    SUPABASE_URL = "SUPABASE_URL"
    SUPABASE_KEY = "SUPABASE_KEY"
    SUPABASE_JWT_SECRET = "SUPABASE_JWT_SECRET"

    # Application configuration
    DEBUG = "DEBUG"
    TESTING = "TESTING"
    LOG_LEVEL = "LOG_LEVEL"
    USE_GSM = "USE_GSM"

    # Google Cloud
    GCP_PROJECT_ID = "GCP_PROJECT_ID"


class Defaults:
    """Default configuration values"""

    # Application metadata
    APP_NAME = "Supabase Auth API"
    APP_VERSION = "0.1.0"
    APP_DESCRIPTION = "Production-ready authentication API with Supabase"

    # API configuration
    API_V1_STR = "/api/v1"

    # CORS
    CORS_ORIGINS = ["*"]

    # Logging
    LOG_LEVEL = "INFO"

    # Boolean defaults
    DEBUG = False
    TESTING = False
    USE_GSM = False


class Validation:
    """Validation rules and constraints"""

    # Password requirements
    MIN_PASSWORD_LENGTH = 8


class Supabase:
    """Supabase-specific constants"""

    # Secret names for GSM
    REQUIRED_SECRETS = ["SUPABASE_URL", "SUPABASE_KEY", "SUPABASE_JWT_SECRET"]

    # User metadata fields
    FULL_NAME_FIELD = "full_name"

    # GSM secret path template
    SECRET_PATH_TEMPLATE = "projects/{project_id}/secrets/{secret_name}/versions/latest"


class OAuth:
    """OAuth provider constants"""

    GOOGLE = "google"
