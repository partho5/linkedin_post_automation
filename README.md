# LinkedIn Content Automation API

## Quick Start
1. Clone repository
2. Create `.env` file with credentials (see .env.example)
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run the server:
   ```bash
   uvicorn main:app --host 127.0.0.1 --port 8001
   ```

## LinkedIn OAuth Setup
1. Get authorization code from LinkedIn OAuth URL
2. Exchange code for tokens using `/api/v1/linkedin/exchange-token`
3. Post content using `/api/v1/linkedin/post`

## Endpoints

### LinkedIn OAuth Endpoints
- **POST** `/api/v1/linkedin/exchange-token` — Exchange authorization code for access tokens
- **POST** `/api/v1/linkedin/post` — Post content to LinkedIn (with/without images)

### Content Generation Endpoints
- **POST** `/api/v1/generate-content` — Create LinkedIn post content
- **POST** `/api/v1/generate-image` — Generate accompanying image

### Legacy Endpoints (Environment Variable Based)
- **POST** `/api/v1/post-linkedin` — Publish to LinkedIn (uses LINKEDIN_ACCESS_TOKEN)
- **POST** `/api/v1/schedule-post` — Schedule future post
- **GET** `/api/v1/status/{job_id}` — Check pipeline status

### Utility Endpoints
- **GET** `/api/v1/health-check` — Service health check

## Authentication
Bearer token via `BASIC_AUTH_TOKEN` in `.env` file. Pass as `Authorization: Bearer <token>` header.

## Environment Variables

### Required for OAuth Flow
- `BASIC_AUTH_TOKEN` — API access token
- `LINKEDIN_CLIENT_ID` — LinkedIn OAuth app client ID
- `LINKEDIN_CLIENT_SECRET` — LinkedIn OAuth app client secret
- `LINKEDIN_CALLBACK_URL` — LinkedIn OAuth redirect URI

### Optional (for legacy endpoints)
- `LINKEDIN_ACCESS_TOKEN` — LinkedIn API token (for legacy posting)

### AI Services
- `OPENAI_API_KEY` — OpenAI API key

## Usage Examples

### OAuth Flow (Recommended)
```bash
# 1. Exchange authorization code for tokens
curl -X POST "http://127.0.0.1:8001/api/v1/linkedin/exchange-token" \
  -H "Authorization: Bearer your_api_token" \
  -H "Content-Type: application/json" \
  -d '{"auth_code": "your_linkedin_auth_code"}'

# 2. Post content (text-only)
curl -X POST "http://127.0.0.1:8001/api/v1/linkedin/post" \
  -H "Authorization: Bearer your_api_token" \
  -H "Content-Type: application/json" \
  -d '{"content": "Your LinkedIn post content"}'

# 3. Post with image
curl -X POST "http://127.0.0.1:8001/api/v1/linkedin/post" \
  -H "Authorization: Bearer your_api_token" \
  -H "Content-Type: application/json" \
  -d '{"content": "Your post with image", "image_path": "assets/media/image/photo.png"}'
```

### Legacy Flow
```bash
# Post using environment variable token
curl -X POST "http://127.0.0.1:8001/api/v1/post-linkedin" \
  -H "Authorization: Bearer your_api_token" \
  -H "Content-Type: application/json" \
  -d '{"content": "Your post content", "image": "optional_image_path"}'
```

## Features
- ✅ **LinkedIn OAuth Integration** - Secure token management
- ✅ **Text & Image Posts** - Support for both content types
- ✅ **URL & Local Images** - Upload from web or local files
- ✅ **Automatic Token Refresh** - No manual token management
- 🔄 **Content Generation** - AI-powered post creation (in development)
- 🔄 **Image Generation** - AI-generated visuals (in development)
- 🔄 **Post Scheduling** - Automated posting (in development)

## Notes
- OAuth tokens are automatically stored in `assets/linkedin_tokens.json`
- Image paths support both local files and public URLs
- All endpoints require Bearer token authentication
- See `.env.example` for complete configuration 