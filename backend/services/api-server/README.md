# Supabase Auth API

A production-ready authentication API scaffolding template using FastAPI and Supabase with Google OAuth support and Google Secret Manager integration.

## Features

- 🔐 **Email/Password Authentication** - Complete signup, login, logout, password reset
- 🌟 **Google OAuth** - Social login with Google authentication (PKCE flow)
- 🛡️ **JWT Token Validation** - Production-level security with proper token verification
- 🌐 **Supabase Integration** - Direct integration with Supabase Auth
- 🔑 **Google Secret Manager** - Production secret management support
- ⚡ **FastAPI** - Modern, fast Python web framework with async support
- 📝 **Auto Documentation** - Interactive API docs at `/docs`
- 🔧 **Testing Tools** - OAuth testing interface included

## Architecture Overview

This API follows a clean architecture pattern:

- **FastAPI** handles HTTP requests and responses
- **Supabase** manages authentication, user sessions, and OAuth flows
- **Google Secret Manager** securely stores production credentials
- **Pydantic** validates all request/response data
- **PKCE OAuth Flow** ensures secure Google authentication

## Complete Setup Guide

### Prerequisites

- Python 3.10+ installed
- A Supabase account
- A Google Cloud Platform account (for OAuth and optional GSM)
- Basic knowledge of environment variables

### 1. Clone and Install

```bash
# Clone the repository
git clone <your-repo-url>
cd supabase-api-scaffolding-template

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Supabase Project Setup

#### Step 1: Create Supabase Project

1. Go to [supabase.com](https://supabase.com) and sign up/login
2. Click "New Project"
3. Choose your organization and region
4. Set a strong database password (save this!)
5. Wait for project creation (2-3 minutes)

#### Step 2: Configure Authentication Settings

1. In your Supabase dashboard, go to **Authentication → Settings**
2. Configure the following:

**Email Authentication:**

- ✅ Enable email confirmations (recommended)
- ✅ Enable password recovery
- Set "Confirm email" to your preference (recommended: enabled)

**Security Settings:**

- Set JWT expiry to `3600` (1 hour) or your preference
- Enable Row Level Security (RLS) on auth tables

**URL Configuration:**

- Set Site URL to your production domain (e.g., `https://yourdomain.com`)
- Add Redirect URLs for development: `http://localhost:3000`, `http://localhost:8000`

#### Step 3: Get Supabase Credentials

1. Go to **Settings → API**
2. Copy the following values (you'll need these for your `.env` file):

```
Project URL: https://your-project-ref.supabase.co
anon/public key: eyJhbGc... (starts with eyJ)
JWT Secret: your-jwt-secret-here (used for token verification)
```

### 3. Google Cloud Platform Setup (OAuth)

#### Step 1: Create GCP Project

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project or select existing one
3. Note your Project ID (you'll need this for GSM)

#### Step 2: Enable Required APIs

```bash
# Using gcloud CLI (recommended)
gcloud services enable secretmanager.googleapis.com
gcloud services enable oauth2.googleapis.com

# Or enable manually in console:
# Go to APIs & Services → Library → Search for "Secret Manager API" → Enable
# Search for "Google+ API" → Enable (legacy, but required for OAuth)
```

#### Step 3: Create OAuth 2.0 Credentials

1. Go to **APIs & Services → Credentials**
2. Click **+ CREATE CREDENTIALS → OAuth 2.0 Client IDs**
3. Set Application type to **Web application**
4. Name it something like "Supabase Auth API"

**Important URLs to configure:**

```
Authorized JavaScript origins:
- https://your-project-ref.supabase.co (replace with your actual Supabase URL)
- http://localhost:3000 (for testing)

Authorized redirect URIs:
- https://your-project-ref.supabase.co/auth/v1/callback (CRITICAL - must match exactly)
```

5. Save and copy your **Client ID** and **Client Secret**

#### Step 4: Configure Google OAuth in Supabase

1. In Supabase dashboard, go to **Authentication → Providers**
2. Find **Google** and click to configure
3. Enable the provider
4. Enter your Google OAuth **Client ID** and **Client Secret**
5. Save configuration

### 4. Environment Configuration

Create a `.env` file in the project root with these variables:

```env
# ===== SUPABASE CONFIGURATION (REQUIRED) =====
# Your Supabase project URL - get from Supabase Settings → API
SUPABASE_URL=https://your-project-ref.supabase.co

# Supabase anon/public key - get from Supabase Settings → API
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# Supabase JWT secret - get from Supabase Settings → API
# Used for verifying JWT tokens on the server side
SUPABASE_JWT_SECRET=your-jwt-secret-here

# ===== GOOGLE CLOUD CONFIGURATION (PRODUCTION) =====
# Set to true in production to use Google Secret Manager for secrets
USE_GSM=false

# Your GCP Project ID - required if USE_GSM=true
GCP_PROJECT_ID=your-gcp-project-id

# ===== APPLICATION SETTINGS (OPTIONAL) =====
# Enable debug logging and error details
DEBUG=false

# Enable testing mode (affects some behavior)
TESTING=false

# Logging level: DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_LEVEL=INFO

# CORS origins - domains allowed to make requests to your API
# Use ["*"] for development, specific domains for production
CORS_ORIGINS=["*"]
```

#### Environment Variables Explained

| Variable              | Purpose                               | Required           | Example                      |
| --------------------- | ------------------------------------- | ------------------ | ---------------------------- |
| `SUPABASE_URL`        | Your Supabase project endpoint        | ✅ Yes             | `https://abc123.supabase.co` |
| `SUPABASE_KEY`        | Public API key for Supabase client    | ✅ Yes             | `eyJhbGc...`                 |
| `SUPABASE_JWT_SECRET` | Secret for validating JWT tokens      | ✅ Yes             | `your-jwt-secret`            |
| `USE_GSM`             | Enable Google Secret Manager          | 🔧 Production      | `false` (dev), `true` (prod) |
| `GCP_PROJECT_ID`      | Google Cloud project identifier       | 🔧 If USE_GSM=true | `my-project-123`             |
| `DEBUG`               | Enable debug mode and verbose logging | ❌ Optional        | `false`                      |
| `TESTING`             | Enable testing mode                   | ❌ Optional        | `false`                      |
| `LOG_LEVEL`           | Logging verbosity level               | ❌ Optional        | `INFO`                       |
| `CORS_ORIGINS`        | Allowed request origins               | ❌ Optional        | `["https://myapp.com"]`      |

### 5. Google Secret Manager Setup (Production)

For production deployments, you can store sensitive credentials in Google Secret Manager instead of environment variables.

#### Step 1: Create Secrets in GSM

```bash
# Authenticate with Google Cloud
gcloud auth login
gcloud config set project YOUR_GCP_PROJECT_ID

# Create secrets (replace with your actual values)
echo -n "https://your-project-ref.supabase.co" | gcloud secrets create SUPABASE_URL --data-file=-
echo -n "your_supabase_anon_key" | gcloud secrets create SUPABASE_KEY --data-file=-
echo -n "your_supabase_jwt_secret" | gcloud secrets create SUPABASE_JWT_SECRET --data-file=-
```

#### Step 2: Configure Service Account (Production)

```bash
# Create service account
gcloud iam service-accounts create supabase-auth-api

# Grant Secret Manager access
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:supabase-auth-api@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"

# For Cloud Run/GCE, assign this service account to your instance
```

#### Step 3: Production Environment Variables

```env
# Production .env file (minimal)
USE_GSM=true
GCP_PROJECT_ID=your-gcp-project-id
DEBUG=false
LOG_LEVEL=WARNING
CORS_ORIGINS=["https://yourdomain.com"]
```

### 6. Run and Test

#### Start the Development Server

```bash
# Development with auto-reload
uvicorn src.api.api:app --reload --host 0.0.0.0 --port 8000

# Production
uvicorn src.api.api:app --host 0.0.0.0 --port 8000 --workers 4
```

#### Access the API

- **API Base URL**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

#### Test OAuth Flow

1. Navigate to `src/tests/oauth/oauth_test.html`
2. Serve it locally:
   ```bash
   cd src/tests/oauth
   python -m http.server 3000
   ```
3. Open http://localhost:3000/oauth_test.html
4. Click "Start Google OAuth" to test the flow

## API Endpoints Reference

### Authentication Endpoints

| Method | Endpoint                      | Description               | Request Body                   |
| ------ | ----------------------------- | ------------------------- | ------------------------------ |
| `POST` | `/api/v1/auth/signup`         | Register new user         | `{email, password, full_name}` |
| `POST` | `/api/v1/auth/login`          | Login with email/password | `{email, password}`            |
| `POST` | `/api/v1/auth/logout`         | Logout current user       | Bearer token required          |
| `POST` | `/api/v1/auth/reset-password` | Request password reset    | `{email}`                      |
| `GET`  | `/api/v1/auth/session-check`  | Validate current session  | Bearer token required          |

### OAuth Endpoints

| Method | Endpoint                      | Description           | Request Body                         |
| ------ | ----------------------------- | --------------------- | ------------------------------------ |
| `POST` | `/api/v1/auth/oauth/login`    | Initiate Google OAuth | `{provider: "google", redirect_url}` |
| `POST` | `/api/v1/auth/oauth/callback` | Handle OAuth callback | `{provider, code, redirect_url}`     |

### System Endpoints

| Method | Endpoint  | Description  |
| ------ | --------- | ------------ |
| `GET`  | `/health` | Health check |

## Authentication Flow

### Email/Password Flow

1. **Signup**: `POST /auth/signup` → User created in Supabase
2. **Login**: `POST /auth/login` → Returns JWT access/refresh tokens
3. **Protected Requests**: Include `Authorization: Bearer <access_token>` header
4. **Logout**: `POST /auth/logout` → Invalidates session

### Google OAuth Flow (PKCE)

1. **Initiate**: `POST /auth/oauth/login` → Returns Google OAuth URL
2. **Redirect**: User authenticates with Google
3. **Callback**: Google redirects with authorization code
4. **Exchange**: `POST /auth/oauth/callback` → Returns JWT tokens
5. **Protected Requests**: Use JWT tokens same as email/password flow

## Project Structure

```
supabase-api-scaffolding-template/
├── src/
│   ├── api/
│   │   ├── endpoints/
│   │   │   └── auth.py          # All authentication endpoints
│   │   ├── dependencies.py      # JWT validation, auth dependencies
│   │   ├── router.py            # API route configuration
│   │   └── api.py               # FastAPI app configuration
│   ├── core/
│   │   ├── config.py            # Settings and configuration
│   │   ├── constants.py         # Application constants
│   │   ├── messages.py          # User-facing messages
│   │   ├── secrets.py           # Google Secret Manager integration
│   │   └── supabase_client.py   # Supabase client singleton
│   ├── models/
│   │   └── auth.py              # Pydantic models for requests/responses
│   ├── services/
│   │   └── auth_service.py      # Authentication business logic
│   └── tests/
│       └── oauth/
│           ├── oauth_test.html   # Interactive OAuth testing
│           └── README.md         # OAuth testing guide
├── .env                         # Environment variables (create this)
├── .gitignore                   # Git ignore rules
├── requirements.txt             # Python dependencies
└── README.md                    # This file
```

## Troubleshooting

### Common Issues

**"redirect_uri_mismatch" OAuth error:**

- Check that your Google Cloud Console redirect URI exactly matches: `https://your-project-ref.supabase.co/auth/v1/callback`
- Ensure no trailing slashes or typos

**"Invalid JWT" errors:**

- Verify `SUPABASE_JWT_SECRET` is correct
- Check token expiration settings in Supabase
- Ensure Bearer token format: `Authorization: Bearer <token>`

**GSM authentication errors:**

- Verify service account has `roles/secretmanager.secretAccessor`
- Check `GCP_PROJECT_ID` matches your actual project
- Ensure secrets exist in Secret Manager

**CORS errors in browser:**

- Add your frontend domain to `CORS_ORIGINS`
- For development, use `["*"]` temporarily

### Debugging Tips

1. **Enable debug logging:**

   ```env
   DEBUG=true
   LOG_LEVEL=DEBUG
   ```

2. **Check Supabase logs:**

   - Go to Supabase Dashboard → Logs → Auth logs

3. **Test individual endpoints:**

   - Use the interactive docs at `/docs`
   - Test with curl or Postman

4. **Verify OAuth setup:**
   - Use the provided test page at `src/tests/oauth/oauth_test.html`

## Production Checklist

Before deploying to production:

- [ ] Set `USE_GSM=true` and configure Google Secret Manager
- [ ] Update `CORS_ORIGINS` to specific domains
- [ ] Set `DEBUG=false` and `LOG_LEVEL=WARNING`
- [ ] Configure proper SSL/TLS certificates
- [ ] Set up monitoring and logging
- [ ] Test OAuth flow with production URLs
- [ ] Configure Supabase RLS policies if using database
- [ ] Set up backup/disaster recovery for secrets

## Security Considerations

- **JWT Secrets**: Never commit JWT secrets to version control
- **Environment Variables**: Use `.env` files locally, GSM in production
- **CORS**: Restrict to specific domains in production
- **HTTPS**: Always use HTTPS in production for OAuth
- **Token Expiry**: Configure appropriate JWT expiration times
- **Rate Limiting**: Consider adding rate limiting for auth endpoints

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly (especially OAuth flow)
5. Submit a pull request

## Development

### Code Quality

This project uses pre-commit hooks for automatic code formatting and validation:

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install

# Run hooks on all files
pre-commit run --all-files

# Run individual tools
ruff check src/         # linting
ruff format src/        # formatting
mypy src/              # type checking
pytest src/tests/      # tests

# Bypass hooks (emergency only)
git commit --no-verify -m "message"
```

## License

MIT License
