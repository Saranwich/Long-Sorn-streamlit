# constants.py & messages.py - Context Documentation

## Purpose

This module group provides centralized constants and user-facing messages for the Supabase Auth API. The `constants.py` file defines application-wide configuration constants, environment variable names, validation rules, and service-specific constants organized into logical classes. The `messages.py` file contains all user-facing text including error messages, success messages, and internal log messages, organized for maintainability and future localization support. Together, they ensure consistent messaging and configuration throughout the application.

## Usage Summary

**File Locations**:

- `src/core/constants.py` - Application constants and configuration defaults
- `src/core/messages.py` - User-facing and internal messages

**Primary Use Cases**:

- Providing centralized configuration constants and defaults
- Defining environment variable names for consistent access
- Setting validation rules and constraints (password length, etc.)
- Storing Supabase-specific constants like metadata field names
- Providing standardized error messages for consistent user experience
- Supplying internal log messages for debugging and audit trails
- Supporting future internationalization through centralized message management

**Key Dependencies**:

- No external dependencies - these are standalone modules that provide constants and messages to other parts of the system

## Key Functions or Classes

**Constants Classes:**

- **EnvVars**: Environment variable names for configuration (SUPABASE_URL, DEBUG, etc.)
- **Defaults**: Default configuration values for app metadata, API paths, CORS, and boolean settings
- **Validation**: Validation rules and constraints like minimum password length requirements
- **Supabase**: Supabase-specific constants including required secrets, metadata field names, and GSM path templates
- **OAuth**: OAuth provider constants for supported authentication providers

**Message Classes:**

- **ErrorMessages**: User-facing error messages for authentication failures, invalid tokens, and other error conditions
- **SuccessMessages**: User-facing success messages for completed operations like logout and password reset
- **LogMessages**: Internal log messages for user actions, settings loading, secret management, and JWT validation

## Usage Notes

- All constants are organized into logical classes to prevent naming conflicts and improve discoverability
- Environment variable names are centralized to ensure consistency across the application
- Default values provide sensible fallbacks for all configuration options
- Error messages are designed to be user-friendly while avoiding information disclosure
- Log messages include placeholders for dynamic content using Python string formatting
- The constants support both development and production environments
- Message organization facilitates future localization efforts
- Validation constants ensure consistent rules across different parts of the application
- OAuth constants are designed to be easily extensible for additional providers

## Dependencies & Integration

These modules are foundational and used throughout the entire application:

- **Configuration System**: Uses constants for defaults and environment variable names
- **Authentication Service**: Uses OAuth constants, validation rules, and all message types
- **API Endpoints**: Uses error and success messages for consistent user communication
- **Secret Management**: Uses Supabase constants for GSM integration and required secrets
- **Settings Management**: Uses environment variable names and default values
- **Logging System**: Uses log messages for consistent internal communication
- **Validation**: Uses validation constants for input validation across the application

These modules have no dependencies and serve as the foundation for other modules, ensuring consistent configuration and messaging throughout the system.

## Changelog

### [2025-01-19]

- Context documentation completed
- Documented constants organization and message management
- Added details about localization support and validation rules

---

_This document is maintained by Cursor. Last updated: 2025-01-19_
