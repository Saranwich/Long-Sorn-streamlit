# secrets.py - Context Documentation

## Purpose

This module provides secure secret management functionality with Google Secret Manager (GSM) integration and graceful fallback to environment variables. It handles the retrieval, caching, and loading of sensitive configuration data like API keys, database credentials, and JWT secrets. The module is designed to work seamlessly in both development (using environment variables) and production (using GSM) environments, providing a unified interface for secret access throughout the application.

## Usage Summary

**File Location**: `src/core/secrets.py`

**Primary Use Cases**:

- Retrieving secrets from Google Secret Manager with automatic fallback to environment variables
- Loading critical Supabase secrets (URL, API key, JWT secret) at application startup
- Caching secret values to minimize API calls to GSM
- Determining whether to use GSM or environment variables based on configuration
- Providing secure secret access for authentication and database operations

**Key Dependencies**:

- `logging`: Used for tracking secret retrieval operations, errors, and fallback scenarios for security auditing
- `os`: Provides access to environment variables for fallback secret storage and configuration
- `functools.lru_cache`: Implements caching for secret values to reduce GSM API calls and improve performance
- `typing.Optional`: Provides type hints for optional project ID parameter in secret retrieval
- `google.cloud.secretmanager`: Google Cloud client library for accessing Secret Manager API
- `src.core.constants.EnvVars`: Environment variable name constants for consistent configuration
- `src.core.constants.Supabase`: Supabase-specific constants including required secret names and GSM path templates
- `src.core.messages.LogMessages`: Standardized log messages for secret management operations

## Key Functions or Classes

**Key Functions:**

- **get_secret(secret_name, project_id)**: Retrieves a specific secret from GSM with LRU caching, automatically falls back to environment variables if GSM access fails
- **load_secrets_from_gsm()**: Loads all critical Supabase secrets from GSM into environment variables at application startup, ensuring they're available for the Settings class
- **should_use_gsm()**: Determines whether Google Secret Manager should be used based on the USE_GSM environment variable configuration

## Usage Notes

- The `get_secret` function is decorated with `@lru_cache` to prevent repeated API calls for the same secret
- GSM integration gracefully degrades to environment variables if GSM is unavailable or misconfigured
- All secret access operations are logged for security auditing and debugging purposes
- The module automatically loads required Supabase secrets at startup when GSM is enabled
- Project ID can be provided explicitly or read from the GCP_PROJECT_ID environment variable
- Secret names must match exactly between GSM and the constants defined in the Supabase class
- Empty or missing secrets from GSM trigger warnings but don't crash the application
- The module follows the principle of "secure by default" with comprehensive error handling

## Dependencies & Integration

This module is a critical component of the application's security infrastructure:

- **Configuration System**: Used by `config.py` to load secrets before Settings initialization
- **Authentication**: Provides JWT secrets and Supabase credentials for auth operations
- **Database Access**: Supplies database connection credentials through Supabase configuration
- **Production Deployment**: Essential for secure secret management in Google Cloud environments
- **Development Workflow**: Allows developers to use environment variables locally while production uses GSM
- **Logging System**: Integrates with the application's logging for security audit trails

The module is imported and used early in the application lifecycle, typically before any other services are initialized.

## Changelog

### [2025-01-19]

- Context documentation completed
- Documented GSM integration and fallback mechanisms
- Added security and caching considerations

---

_This document is maintained by Cursor. Last updated: 2025-01-19_
