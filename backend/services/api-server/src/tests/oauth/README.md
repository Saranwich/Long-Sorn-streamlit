# OAuth Testing

This directory contains tools for testing Google OAuth integration with Supabase.

## OAuth PKCE Flow

This implementation uses **Supabase's built-in PKCE handling** with a backend callback for security.

### How It Works

1. **Initiate OAuth**: Call `/api/v1/auth/oauth/login` to get Google OAuth URL
2. **Redirect to Google**: User authenticates with Google
3. **Google Returns Code**: User returns with authorization code in URL
4. **Exchange Code**: Frontend calls `/api/v1/auth/oauth/callback` to exchange code for tokens
5. **Backend Handles PKCE**: Supabase exchanges code for session tokens using stored PKCE verifier

### API Endpoints

- `POST /api/v1/auth/oauth/login` - Get Google OAuth URL

  - Request: `{"provider": "google", "redirect_url": "http://localhost:3000/oauth_test.html"}`
  - Response: `{"auth_url": "https://accounts.google.com/oauth/..."}`

- `POST /api/v1/auth/oauth/callback` - Exchange authorization code for tokens
  - Request: `{"provider": "google", "code": "auth_code_here", "redirect_url": "..."}`
  - Response: `{"user": {...}, "token": {"access_token": "...", "refresh_token": "..."}}`

## Testing

1. **Start your FastAPI server**:

   ```bash
   cd /path/to/your/project
   python -m uvicorn src.main:app --reload --port 8000
   ```

2. **Serve the test page**:

   ```bash
   cd src/tests/oauth
   python -m http.server 3000
   ```

3. **Open browser**: http://localhost:3000/oauth_test.html

4. **Test OAuth flow**:
   - Click "🚀 Start Google OAuth"
   - Authenticate with Google
   - Get redirected back with success tokens in URL

### Success Response

After successful OAuth, the test page will display tokens received from your backend:

```json
{
  "user": {
    "id": "user_id",
    "email": "user@example.com",
    "full_name": "User Name"
  },
  "token": {
    "access_token": "jwt_token_here",
    "refresh_token": "refresh_token_here",
    "token_type": "bearer"
  }
}
```

## Configuration Required

### Google Cloud Console

1. Enable Google+ API
2. Create OAuth 2.0 credentials
3. Add authorized redirect URI: `https://your-project.supabase.co/auth/v1/callback`

### Supabase Dashboard

1. Go to Authentication > Providers > Google
2. Enable Google provider
3. Add your Google OAuth Client ID and Secret

### Environment Variables

No Google OAuth environment variables needed in your app - Supabase handles the credentials!

## Troubleshooting

**Not getting tokens?**

- Check Supabase provider configuration in dashboard
- Verify Google Cloud Console redirect URI: `https://your-project.supabase.co/auth/v1/callback`
- Check browser network tab for API errors
- Ensure FastAPI server is running on port 8000

**Getting authorization code but token exchange fails?**

- Check that the same Supabase client instance is used (singleton pattern)
- Verify the redirect URL matches exactly between login and callback requests
