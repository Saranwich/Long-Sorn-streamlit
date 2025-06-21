# config.py & supabase_client.py - Context Documentation

## Purpose

This module group handles application configuration management and Supabase client instantiation. The `config.py` file provides centralized settings management with environment variable loading and optional Google Secret Manager integration, while `supabase_client.py` provides a singleton factory pattern for the Supabase client to maintain PKCE state across authentication flows. Together, they form the foundation for secure configuration management and database connectivity.

## Usage Summary

**File Locations**:

- `src/core/config.py` - Application settings and configuration
- `src/core/supabase_client.py` - Supabase client factory

**Primary Use Cases**:

- Loading application settings from environment variables or Google Secret Manager
- Providing centralized configuration access throughout the application
- Creating and maintaining a singleton Supabase client instance
- Preserving PKCE state during OAuth authentication flows
- Managing CORS, logging, and other application-wide settings

**Key Dependencies**:

- `supabase.Client`: Supabase client interface for database and auth operations
- `supabase.create_client`: Factory function to create Supabase client instances
- `src.core.config.settings`: Global settings instance used throughout the application
- `pydantic_settings.BaseSettings`: Provides validation and environment variable loading
- `src.core.secrets.load_secrets_from_gsm`: Google Secret Manager integration for secure secret loading
- `src.core.constants`: Application defaults and configuration constants

## Key Functions or Classes

**Classes:**

- **Settings**: Pydantic settings class that handles environment variable loading, validation, and Google Secret Manager integration

**Key Functions:**

- **get_settings()**: Factory function that loads secrets from GSM if enabled and returns configured Settings instance
- **get_supabase_client()**: Singleton factory that creates and reuses a Supabase client instance to preserve PKCE state
- **should_use_testing()**: Helper function to determine if the application is running in testing mode
- **should_use_gsm()**: Helper function (in secrets.py) to determine if Google Secret Manager should be used

## Usage Notes

- The Settings class uses Pydantic for automatic validation and type conversion of environment variables
- Google Secret Manager integration is optional and controlled by the `USE_GSM` environment variable
- The Supabase client is implemented as a singleton to preserve PKCE state during OAuth flows
- All configuration values have sensible defaults defined in the constants module
- The settings instance is created at module import time for global access
- Log level is automatically configured based on the settings
- CORS origins can be configured but default to allowing all origins for development
- Secret loading fails gracefully and falls back to environment variables if GSM is unavailable

## Dependencies & Integration

This configuration system is used throughout the entire application:

- **Authentication Service**: Uses Supabase client for auth operations and settings for JWT secrets
- **API Endpoints**: Uses settings for CORS configuration and app metadata
- **Secret Management**: Integrates with Google Secret Manager for production secret loading
- **Logging**: Uses settings to configure application-wide log levels
- **Database Operations**: All database access goes through the singleton Supabase client
- **Testing**: Uses testing mode detection for test-specific configuration

The singleton pattern for the Supabase client is critical for OAuth flows, as PKCE state must be preserved across requests.

## Changelog

### [2025-01-19]

- Context documentation completed
- Documented configuration management and Supabase client factory
- Added details about GSM integration and PKCE state preservation

---

_This document is maintained by Cursor. Last updated: 2025-01-19_
