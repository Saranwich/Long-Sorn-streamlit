# auth.py - Context Documentation

## Purpose

This module defines the complete set of authentication API endpoints for the Supabase Auth API. It provides RESTful endpoints for user registration, login, logout, password reset, OAuth flows, and session validation. The module handles HTTP request/response processing, error handling, and data formatting while delegating business logic to the authentication service. It serves as the primary interface between client applications and the authentication system, providing comprehensive auth functionality through well-designed REST endpoints.

## Usage Summary

**File Location**: `src/api/endpoints/auth.py`

**Primary Use Cases**:

- Handling user registration and login requests with proper validation
- Managing OAuth authentication flows including Google OAuth with PKCE
- Processing logout requests and session invalidation
- Handling password reset requests and email notifications
- Validating active user sessions and JWT tokens
- Converting service responses to standardized API response formats
- Providing comprehensive error handling with appropriate HTTP status codes

**Key Dependencies**:

- `logging`: Used for tracking authentication events, errors, and security-related activities
- `typing.Any`: Provides type hints for dynamic response data from Supabase
- `fastapi.APIRouter`: Creates the authentication router for organizing related endpoints
- `fastapi.Depends`: Enables dependency injection for services and authentication
- `fastapi.HTTPException`: Used for raising HTTP errors with appropriate status codes
- `fastapi.status`: Provides HTTP status code constants for consistent responses
- `fastapi.security.HTTPAuthorizationCredentials`: Type for Authorization header handling
- `src.api.dependencies`: Authentication dependencies and service factories
- `src.core.constants.Supabase`: Supabase-specific constants for metadata handling
- `src.core.messages`: Error and success messages for consistent user communication
- `src.models.auth`: Pydantic models for request/response validation and serialization
- `src.services.auth_service.AuthService`: Business logic service for authentication operations

## Key Functions or Classes

**Router Object:**

- **router**: FastAPI APIRouter instance that organizes all authentication endpoints

**Helper Functions:**

- **handle_auth_error(e)**: Converts authentication service exceptions to appropriate HTTP exceptions with proper status codes
- **format_auth_response(result)**: Standardizes Supabase auth responses into consistent API response format with user and token data

**API Endpoints:**

- **POST /signup**: User registration endpoint with email, password, and full name validation
- **POST /login**: User authentication endpoint with email/password credentials
- **POST /logout**: Session termination endpoint that invalidates user tokens
- **POST /reset-password**: Password reset initiation endpoint that sends reset emails
- **GET /session-check**: Session validation endpoint for checking token validity
- **POST /oauth/login**: OAuth flow initiation endpoint for Google authentication
- **POST /oauth/callback**: OAuth callback endpoint for handling authorization code exchange

## Usage Notes

- All endpoints use Pydantic models for automatic request validation and response serialization
- Error handling is centralized through the `handle_auth_error` helper function
- OAuth endpoints support PKCE flow for enhanced security in public clients
- Response formatting is standardized through the `format_auth_response` helper
- Login endpoint returns 401 Unauthorized for invalid credentials to prevent user enumeration
- Session check endpoint requires valid JWT token and returns user ID for authorization
- Password reset endpoint always returns success to prevent email enumeration attacks
- OAuth flow preserves state through Supabase's built-in PKCE implementation
- All endpoints include comprehensive logging for security auditing and debugging
- Error responses include descriptive messages while avoiding information disclosure
- Token responses include both access and refresh tokens for complete session management

## Dependencies & Integration

This module serves as the primary API interface and integrates with:

- **Authentication Service**: Delegates all business logic to the AuthService for separation of concerns
- **Dependency Injection**: Uses FastAPI dependencies for service instantiation and authentication
- **Pydantic Models**: Validates all request/response data using the auth models
- **Error Handling**: Provides consistent error responses across all authentication operations
- **OAuth Integration**: Implements complete OAuth flow with Supabase's PKCE support
- **Session Management**: Handles JWT token validation and user session lifecycle
- **API Router**: Integrated into the main API router with '/auth' prefix and 'auth' tags
- **Frontend Applications**: Provides the complete authentication API for client applications
- **Security Middleware**: Works with authentication dependencies for protected endpoints

The module is included in the main API router and serves as the entry point for all authentication-related operations in the system.

## Changelog

### [2025-01-19]

- Context documentation completed
- Documented all authentication endpoints and OAuth flows
- Added comprehensive error handling and security considerations

---

_This document is maintained by Cursor. Last updated: 2025-01-19_
