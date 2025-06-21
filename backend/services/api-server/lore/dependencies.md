# dependencies.py - Context Documentation

## Purpose

This module provides FastAPI dependency injection functions for authentication and authorization throughout the API. It handles JWT token validation, user authentication, and service instantiation using FastAPI's dependency system. The module serves as the security layer that protects endpoints and provides authenticated user context to route handlers. It implements JWT validation with proper error handling and integrates with the authentication service for consistent security across all protected endpoints.

## Usage Summary

**File Location**: `src/api/dependencies.py`

**Primary Use Cases**:

- Validating JWT tokens from Authorization headers in protected endpoints
- Extracting user IDs from validated JWT tokens for authorization
- Providing authenticated user context to route handlers through dependency injection
- Creating AuthService instances for dependency injection in endpoints
- Implementing centralized authentication logic for consistent security

**Key Dependencies**:

- `logging`: Used for tracking authentication attempts, JWT validation failures, and security events
- `typing.Any`: Provides type hints for JWT payload which has dynamic structure
- `fastapi.Depends`: FastAPI's dependency injection system for providing authenticated context
- `fastapi.HTTPException`: Used to raise HTTP 401 Unauthorized errors for invalid tokens
- `fastapi.status`: Provides HTTP status code constants for consistent error responses
- `fastapi.security.HTTPAuthorizationCredentials`: Type for Authorization header credentials
- `fastapi.security.HTTPBearer`: Security scheme for extracting Bearer tokens from headers
- `jose.JWTError`: Exception type for JWT validation errors
- `jose.jwt`: JWT library for token decoding and validation
- `src.core.config.settings`: Application settings including JWT secret for token validation
- `src.core.messages.ErrorMessages`: Standardized error messages for authentication failures
- `src.core.messages.LogMessages`: Standardized log messages for security events
- `src.services.auth_service.AuthService`: Authentication service for dependency injection

## Key Functions or Classes

**Key Functions:**

- **validate_jwt_token(token)**: Core JWT validation function that decodes tokens, verifies signatures, checks expiration, and extracts user ID from the 'sub' claim
- **get_current_user(credentials)**: FastAPI dependency that extracts Bearer token from Authorization header and returns authenticated user ID
- **get_auth_service()**: Factory dependency that creates AuthService instances for injection into route handlers

**Security Objects:**

- **security**: HTTPBearer instance configured for extracting Bearer tokens from Authorization headers

## Usage Notes

- JWT validation includes signature verification, expiration checking, and audience validation
- The 'sub' claim in JWT tokens is used as the user identifier throughout the system
- All JWT validation errors are logged for security monitoring and debugging
- The HTTPBearer security scheme automatically extracts tokens from 'Authorization: Bearer <token>' headers
- Dependencies are designed to be used with FastAPI's `Depends()` function in route definitions
- Authentication failures result in HTTP 401 Unauthorized responses with descriptive error messages
- The module provides centralized authentication logic to ensure consistent security across all endpoints
- JWT audience is validated against 'authenticated' to ensure tokens are intended for this service
- User ID extraction is type-safe and handles missing 'sub' claims gracefully

## Dependencies & Integration

This module is central to the API's security architecture and integrates with:

- **API Endpoints**: Used as dependencies in protected route handlers to ensure authentication
- **JWT Token System**: Validates tokens issued by Supabase Auth using the configured JWT secret
- **Authentication Service**: Provides AuthService instances to endpoints for auth operations
- **Error Handling**: Integrates with the application's error handling for consistent responses
- **Logging System**: Provides security audit trails for authentication attempts and failures
- **Configuration System**: Uses JWT secrets from settings for token validation
- **FastAPI Framework**: Leverages FastAPI's dependency injection for clean separation of concerns

The module is imported by route handlers that require authentication and serves as the gateway for all protected API operations.

## Changelog

### [2025-01-19]

- Context documentation completed
- Documented JWT validation and dependency injection patterns
- Added security considerations and integration details

---

_This document is maintained by Cursor. Last updated: 2025-01-19_
