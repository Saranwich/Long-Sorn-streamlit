# auth_service.py - Context Documentation

## Purpose

This Python module provides a comprehensive authentication service that handles user registration, login, logout, password reset, and OAuth integration using Supabase Auth. The AuthService class serves as the primary interface for all authentication operations in the system, providing both traditional email/password authentication and OAuth flows (currently supporting Google). It encapsulates Supabase authentication operations and provides standardized error handling and logging.

## Usage Summary

**File Location**: `src/services/auth_service.py`

**Primary Use Cases**:

- User registration with email/password authentication
- User login/logout operations
- Password reset functionality
- OAuth authentication flow (Google provider)
- OAuth callback handling
- Building standardized authentication response dictionaries

**Key Dependencies**:

- `logging`: Used for tracking authentication events, errors, and user activities for audit and debugging purposes
- `typing.Any`: Provides type hints for Supabase response objects which have dynamic structures
- `src.core.constants.OAuth`: Contains OAuth provider constants (e.g., Google provider identifier)
- `src.core.constants.Supabase`: Contains Supabase-specific constants like user metadata field names
- `src.core.messages.ErrorMessages`: Provides standardized error messages for authentication failures
- `src.core.messages.LogMessages`: Provides standardized log messages for authentication events
- `src.core.supabase_client.get_supabase_client`: Factory function to get the configured Supabase client
- `src.models.auth.UserCreate`: Pydantic model for user registration data validation
- `src.models.auth.UserLogin`: Pydantic model for user login data validation

## Key Functions or Classes

**Classes:**

- **AuthService**: Main service class that encapsulates all authentication operations using Supabase Auth. Handles user lifecycle operations, OAuth flows, and provides consistent response formatting.

**Key Functions:**

- \***\*init**(self)\*\*: Initializes the AuthService with a Supabase client instance obtained from the client factory
- **signup(self, user_data: UserCreate)**: Registers a new user with email, password, and full name, storing user metadata in Supabase
- **login(self, user_data: UserLogin)**: Authenticates existing users with email/password credentials
- **logout(self, token: str)**: Signs out the current user and invalidates their session
- **request_password_reset(self, email: str)**: Initiates password reset flow by sending reset email
- **oauth_login(self, provider: str, redirect_url: str)**: Initiates OAuth login flow using PKCE for secure authentication
- **handle_oauth_callback(self, provider: str, code: str, redirect_url: str)**: Handles OAuth callback and exchanges authorization code for session
- **\_build_auth_dict(self, auth_response)**: Internal helper that standardizes Supabase auth responses into consistent dictionary format

## Usage Notes

- The service handles all Supabase Auth operations asynchronously using async/await patterns
- OAuth implementation uses PKCE (Proof Key for Code Exchange) for enhanced security
- Currently only supports Google OAuth provider, but is designed to be extensible for additional providers
- All operations include comprehensive error handling with standardized error messages
- User metadata (like full_name) is stored in Supabase user_metadata field
- The service provides consistent logging for all authentication events for audit trails
- Response format is standardized with user and session objects for consistent API responses
- Errors are wrapped in ValueError with descriptive messages for proper error propagation
- The service gracefully handles edge cases like missing user metadata or malformed responses

## Dependencies & Integration

This service is a core component of the authentication system and integrates with:

- **Supabase Auth**: Primary authentication provider for user management and session handling
- **API Endpoints**: Used by authentication routes in `src/api/endpoints/` for handling HTTP requests
- **Models**: Validates input using Pydantic models from `src/models/auth.py`
- **Core Configuration**: Relies on constants and configuration from `src/core/`
- **Middleware**: Authentication responses are used by authorization middleware for protected routes
- **Client Factory**: Uses the Supabase client factory for consistent client configuration

The service is imported and used by FastAPI route handlers to process authentication requests and is essential for the JWT-based authorization system throughout the application.

## Changelog

### [2025-01-19]

- Context documentation completed
- Documented all authentication methods and OAuth flow
- Added comprehensive usage notes and integration details

---

_This document is maintained by Cursor. Last updated: 2025-01-19_
