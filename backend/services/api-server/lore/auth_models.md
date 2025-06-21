# auth.py - Context Documentation

## Purpose

This module defines comprehensive Pydantic data models for authentication operations in the Supabase Auth API. It provides request/response schemas for user registration, login, OAuth flows, password reset, and token management. The models ensure type safety, automatic validation, and consistent data structures throughout the authentication system. They serve as the contract between the API endpoints and the authentication service, providing clear documentation of expected data formats and validation rules.

## Usage Summary

**File Location**: `src/models/auth.py`

**Primary Use Cases**:

- Validating user input for registration, login, and password reset requests
- Defining response schemas for authentication operations and user data
- Providing type safety for OAuth provider selection and flow management
- Structuring token response data with access and refresh tokens
- Ensuring consistent data formats between API endpoints and services
- Supporting automatic API documentation generation through Pydantic integration

**Key Dependencies**:

- `datetime.datetime`: Used for timestamp fields like user creation dates in response models
- `enum.Enum`: Provides type-safe enumeration for OAuth provider selection
- `pydantic.BaseModel`: Base class for all data models providing validation and serialization
- `pydantic.EmailStr`: Specialized string type for email validation with proper format checking
- `pydantic.Field`: Provides field-level validation constraints like minimum length requirements
- `src.core.constants.OAuth`: OAuth provider constants for enum value validation
- `src.core.constants.Validation`: Validation rules like minimum password length requirements

## Key Functions or Classes

**Base Models:**

- **UserBase**: Base schema containing common user fields (email) shared across multiple models

**Request Models:**

- **UserCreate**: User registration schema with email, password, and full name validation
- **UserLogin**: User login schema with email and password fields
- **PasswordResetRequest**: Password reset request schema with email validation
- **OAuthLoginRequest**: OAuth login initiation request with provider and redirect URL
- **OAuthCallbackRequest**: OAuth callback request with provider, authorization code, and redirect URL

**Response Models:**

- **UserResponse**: User data response schema with ID, email, full name, and creation timestamp
- **TokenResponse**: Token response schema with access token, refresh token, and token type
- **AuthResponse**: Complete authentication response combining user data and token information
- **OAuthResponse**: OAuth login response containing the authorization URL

**Enums:**

- **OAuthProvider**: Type-safe enumeration of supported OAuth providers (currently Google)

## Usage Notes

- All models inherit from Pydantic BaseModel for automatic validation and serialization
- Email fields use EmailStr for proper email format validation
- Password fields include minimum length validation based on security requirements
- OAuth provider selection is type-safe through enum usage
- Token response includes both access and refresh tokens with default empty values
- User creation timestamps are optional to handle cases where they might not be available
- The models support both traditional email/password and OAuth authentication flows
- Field validation happens automatically when models are instantiated
- Models provide clear separation between request data (input) and response data (output)
- OAuth models support the complete PKCE flow with proper URL and code handling
- All models are designed to work seamlessly with FastAPI's automatic documentation

## Dependencies & Integration

These models are central to the authentication system and integrate with:

- **API Endpoints**: Used as request/response schemas in FastAPI route definitions
- **Authentication Service**: Validates input data and structures response data
- **FastAPI Framework**: Provides automatic request validation and response serialization
- **Pydantic Validation**: Ensures data integrity and type safety throughout the system
- **OAuth Flows**: Supports both login initiation and callback handling
- **Token Management**: Structures JWT and refresh token responses
- **API Documentation**: Automatically generates OpenAPI/Swagger documentation
- **Frontend Integration**: Provides clear contracts for client applications

The models serve as the data contract between the API layer and the business logic, ensuring consistent and validated data flow throughout the authentication system.

## Changelog

### [2025-01-19]

- Context documentation completed
- Documented all authentication models and their purposes
- Added details about validation rules and OAuth support

---

---

_This document is maintained by Cursor. Last updated: 2025-01-19_
