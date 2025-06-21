# api.py & router.py - Context Documentation

## Purpose

This module group handles the FastAPI application setup and routing configuration for the Supabase Auth API. The `api.py` file creates and configures the main FastAPI application with middleware, CORS settings, and health check endpoints, while `router.py` organizes and includes all API endpoint routers. Together, they form the foundation of the web application, providing the entry point for all HTTP requests and organizing the API structure in a clean, modular way.

## Usage Summary

**File Locations**:

- `src/api/api.py` - Main FastAPI application setup and configuration
- `src/api/router.py` - API router organization and endpoint inclusion

**Primary Use Cases**:

- Creating and configuring the main FastAPI application instance
- Setting up CORS middleware for cross-origin requests
- Organizing API endpoints into logical router groups
- Providing application health check functionality
- Configuring application metadata (title, description, version)
- Including all endpoint routers with appropriate prefixes and tags

**Key Dependencies**:

- `fastapi.FastAPI`: Main FastAPI application class for creating the web application
- `fastapi.APIRouter`: Router class for organizing related endpoints
- `fastapi.middleware.cors.CORSMiddleware`: CORS middleware for handling cross-origin requests
- `src.api.router.api_router`: Main API router that includes all endpoint routers
- `src.api.endpoints.auth`: Authentication endpoints router
- `src.core.config.settings`: Application settings for CORS and metadata configuration

## Key Functions or Classes

**Application Objects:**

- **app**: Main FastAPI application instance configured with metadata and middleware

**Router Objects:**

- **api_router**: Main APIRouter that organizes all endpoint routers with appropriate prefixes

**API Endpoints:**

- **GET /health**: Simple health check endpoint that returns application status and version
- **All /api/v1/** endpoints\*\*: Versioned API endpoints organized under the main router

**Middleware Configuration:**

- **CORSMiddleware**: Configured to handle cross-origin requests with appropriate settings

## Usage Notes

- The FastAPI application is configured with descriptive metadata for automatic documentation
- CORS middleware is configured to allow all origins for development (should be restricted in production)
- All API endpoints are versioned under `/api/v1` prefix for future compatibility
- The health check endpoint is available at the root level for monitoring and load balancer checks
- Router organization follows a modular pattern where each feature has its own router
- Authentication endpoints are grouped under `/auth` prefix with `auth` tags for documentation
- The application uses centralized configuration from the settings module
- Logging is configured at the application level for consistent log formatting
- The router pattern allows for easy addition of new endpoint groups

## Dependencies & Integration

This module group serves as the application foundation and integrates with:

- **Configuration System**: Uses settings for CORS origins and application metadata
- **Authentication Endpoints**: Includes the auth router for all authentication operations
- **Middleware Stack**: Configures CORS and other middleware for request processing
- **Health Monitoring**: Provides health check endpoint for operational monitoring
- **API Documentation**: FastAPI automatically generates OpenAPI/Swagger documentation
- **Frontend Applications**: Serves as the backend API for client applications
- **Load Balancers**: Health check endpoint supports load balancer health checks
- **Development Tools**: CORS configuration supports local development workflows

The application serves as the entry point for all HTTP requests and coordinates the entire API ecosystem.

## Changelog

### [2025-01-19]

- Context documentation completed
- Documented FastAPI application setup and router organization
- Added details about middleware configuration and health checks

---

_This document is maintained by Cursor. Last updated: 2025-01-19_
