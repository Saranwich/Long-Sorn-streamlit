# @track_context("core_constants.md")

"""
User-facing messages for the Supabase Auth API

This module contains all user-facing text organized by category
for better maintainability and localization support.
"""


class ErrorMessages:
    """Error messages shown to users"""

    INVALID_CREDENTIALS = "Invalid email or password"
    INVALID_TOKEN = "Invalid authentication token"
    INVALID_TOKEN_MISSING_USER = "Invalid token: missing user identifier"

    LOGOUT_FAILED = "Failed to log out"
    REGISTRATION_FAILED = "Registration failed"
    AUTHENTICATION_FAILED = "Authentication failed"


class SuccessMessages:
    """Success messages shown to users"""

    LOGOUT_SUCCESS = "Successfully logged out"
    PASSWORD_RESET_SENT = "Password reset email sent"


class LogMessages:
    """Internal log messages"""

    USER_CREATED = "User created: {user_id}"
    USER_LOGGED_IN = "User logged in: {user_id}"
    USER_LOGGED_OUT = "User logged out successfully"

    # Settings loading
    LOADING_FROM_ENV = "Loading settings from environment variables (GSM disabled)"
    LOADING_FROM_GSM = "Loading secrets from Google Secret Manager"
    GSM_ERROR_FALLBACK = "Error loading secrets from GSM: {error}"
    GSM_FALLBACK_WARNING = "Falling back to environment variables"

    # Secret management
    FETCHING_SECRET_GSM = "Fetching {secret_name} from GSM"
    SECRET_RETRIEVED_GSM = "Successfully retrieved secret {secret_name} from GSM"
    SECRET_LOADED_GSM = "Loaded {secret_name} from Google Secret Manager"
    SECRET_EMPTY_WARNING = "Could not load {secret_name} from GSM, value was empty"
    SECRET_ACCESS_ERROR = "Error accessing secret {secret_name}: {error}"

    # JWT validation
    JWT_MISSING_SUB = "Token is valid but missing 'sub' claim"
    JWT_VALIDATION_FAILED = "JWT validation failed: {error}"
