# LinkedIn Content Automation API

## Business Impact & Features

### **Transform Your LinkedIn Presence**
- **10x Content Output**: Generate and post professional LinkedIn content automatically
- **Zero Creative Block**: AI-powered content ideas that resonate with your audience
- **Consistent Brand Voice**: Maintain professional, engaging tone across all posts
- **Time Savings**: Reduce content creation time from hours to minutes

### **Complete Content Pipeline**
- **🎯 Smart Idea Generation**: AI identifies trending topics and industry-relevant content ideas
- **✍️ Professional Content Creation**: Generate engaging LinkedIn posts with proper formatting
- **🖼️ Custom Image Generation**: Create relevant, professional images for each post
- **📱 Automated Posting**: Schedule and publish content directly to LinkedIn
- **📊 Performance Tracking**: Monitor post engagement and pipeline success

### **Business Benefits**
- **Increased Engagement**: Professional, consistent content drives higher LinkedIn engagement
- **Brand Authority**: Regular posting establishes thought leadership in your industry
- **Lead Generation**: Quality content attracts potential clients and business opportunities
- **Time Efficiency**: Focus on core business while maintaining active social presence
- **Scalable Growth**: Automate content creation to support business expansion

### **Perfect For**
- **Entrepreneurs & Business Owners**: Maintain professional LinkedIn presence
- **Marketing Teams**: Scale content creation without additional resources
- **Consultants & Freelancers**: Showcase expertise and attract new clients
- **Sales Professionals**: Generate leads through consistent, valuable content
- **Startups**: Build brand awareness and credibility cost-effectively

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
5. Open browser and visit: `http://127.0.0.1:8001`
6. Click "Authorize LinkedIn" to set up OAuth
7. Enter your OpenAI API key when prompted

## Automated LinkedIn Posting with run.py (Windows PC)

For automated LinkedIn content generation and posting on Windows PC:

### Prerequisites
- Python virtual environment named `linkedin_automation` must be created and activated
- All dependencies installed in the virtual environment
- LinkedIn OAuth and OpenAI API keys configured

### Step 1: Start the Server
First, activate your virtual environment and start the server:
```bash
# Activate virtual environment
source linkedin_automation/Scripts/activate

# Start the server
uvicorn main:app --host 127.0.0.1 --port 8001
```

### Step 2: Run the Automation Script
In a new terminal window, run the automation script:
```bash
# Activate virtual environment (if not already activated)
# source linkedin_automation/Scripts/activate

# Run the automation script
python run.py
```

### What run.py Does
The `run.py` script will:
1. **Check if server is running** on the configured host and port
2. **Start server automatically** if not running (using virtual environment)
3. **Trigger the complete LinkedIn posting workflow**:
   - Generate content ideas
   - Create professional LinkedIn posts
   - Generate relevant images
   - Post to LinkedIn automatically
4. **Display real-time logs** from the server and API responses
5. **Handle errors gracefully** with detailed error messages

### Configuration
Set these environment variables in your `.env` file:
```bash
APP_HOST=127.0.0.1
APP_PORT=8001
BASIC_AUTH_TOKEN=your_auth_token_here
```

### Expected Output
```
LinkedIn Content Automation Runner
========================================
🔍 Checking if server is running on 127.0.0.1:8001...
✅ Server is already running!
🚀 Starting LinkedIn content automation...
📡 API URL: http://127.0.0.1:8001/api/v1/automate-content
⚙️  Configuration: {
  "enable_idea_generation": true,
  "enable_content_generation": true,
  "enable_image_generation": true,
  "enable_posting": true,
  "style_params": "professional and engaging"
}
⏱️  Timeout: 600 seconds
--------------------------------------------------
📡 Making API request...
📝 [SERVER LOG] INFO: Starting content automation pipeline...
📝 [SERVER LOG] INFO: Generating content ideas...
📝 [SERVER LOG] INFO: Creating LinkedIn post...
📝 [SERVER LOG] INFO: Generating image...
📝 [SERVER LOG] INFO: Posting to LinkedIn...
📊 Response Status: 200
✅ Automation pipeline completed successfully!
🎉 Automation completed successfully!
```

## Authentication
All API endpoints require Bearer token authentication. Set `BASIC_AUTH_TOKEN` in your `.env` file and include it in requests:
```
Authorization: Bearer your_api_token
```

## API Endpoints Documentation

### 1. Health Check
**GET** `/api/v1/health-check`

Check if the service is running.

**Response:**
```json
{
  "status": "ok"
}
```

### 2. Generate Content
**POST** `/api/v1/generate-content`

Generate LinkedIn post content using AI.

**Request Body:**
```json
{
  "topic": "string (required)",
  "style_params": "string (optional)"
}
```

**Example Request:**
```json
{
  "topic": "AI in modern business",
  "style_params": "professional and engaging"
}
```

**Response:**
```json
{
  "success": true,
  "content": "Generated LinkedIn post content..."
}
```

### 3. Generate Image
**POST** `/api/v1/generate-image`

Generate an image based on content description.

**Request Body:**
```json
{
  "content_description": "string (required)",
  "style": "string (optional)"
}
```

**Example Request:**
```json
{
  "content_description": "A professional business meeting with diverse team members",
  "style": "modern and corporate"
}
```

**Response:**
```json
{
  "success": true,
  "image_path": "path/to/generated/image.png"
}
```

### 4. Post to LinkedIn (Legacy)
**POST** `/api/v1/post-linkedin`

Post content to LinkedIn using environment variable token.

**Request Body:**
```json
{
  "content": "string (required)",
  "image": "string (optional)"
}
```

**Example Request:**
```json
{
  "content": "This is a test post from the LinkedIn API integration!",
  "image": "assets/media/image/photo.png"
}
```

**Response:**
```json
{
  "success": true,
  "post_id": "urn:li:activity:123456789",
  "message": "Post published successfully"
}
```

### 5. Schedule Post
**POST** `/api/v1/schedule-post`

Schedule a post for future publication.

**Request Body:**
```json
{
  "datetime": "string (required, ISO format)",
  "content": "string (required)",
  "image": "string (optional)"
}
```

**Example Request:**
```json
{
  "datetime": "2024-01-15T10:30:00",
  "content": "Scheduled post content",
  "image": "assets/media/image/photo.png"
}
```

**Response:**
```json
{
  "success": true,
  "task_id": "uuid-string",
  "scheduled_time": "2024-01-15T10:30:00"
}
```

### 6. Check Pipeline Status
**GET** `/api/v1/status/{job_id}`

Check the status of a scheduled job.

**Path Parameters:**
- `job_id`: string (required) - The task ID returned from schedule-post

**Response:**
```json
{
  "found": true,
  "task_id": "uuid-string",
  "status": "pending|running|completed|failed|cancelled",
  "task_type": "post_creation",
  "scheduled_time": "2024-01-15T10:30:00",
  "created_at": "2024-01-15T09:00:00",
  "started_at": "2024-01-15T10:30:00",
  "completed_at": "2024-01-15T10:35:00",
  "retry_count": 0,
  "max_retries": 3,
  "error_message": null,
  "is_running": false,
  "pipeline_stages": ["content_generation", "image_generation", "linkedin_posting"],
  "current_stage": "content_generation",
  "stages_completed": [],
  "estimated_completion": "2024-01-15T10:35:00"
}
```

### 7. LinkedIn OAuth Authorization
**GET** `/api/v1/linkedin/authorize`

Get LinkedIn authorization URL and display authorization page.

**Response:** HTML page with LinkedIn authorization button

### 8. LinkedIn OAuth Callback
**GET** `/auth_callback`

Handle LinkedIn OAuth callback and automatically exchange authorization code for tokens.

**Query Parameters:**
- `code` (required) - Authorization code from LinkedIn
- `state` (optional) - State parameter for CSRF protection

**Response:** HTML page with success message and OpenAI API key configuration

### 9. Save OpenAI API Key
**POST** `/api/v1/save-openai-key`

Save OpenAI API key to .env file.

**Request Body:**
```json
{
  "api_key": "string (required)"
}
```

**Example Request:**
```json
{
  "api_key": "sk-your-openai-api-key-here"
}
```

**Response:**
```json
{
  "success": true,
  "message": "OpenAI API key saved successfully"
}
```

### 10. LinkedIn OAuth Token Exchange (Legacy)
**POST** `/api/v1/linkedin/exchange-token`

Exchange LinkedIn authorization code for access tokens (manual method).

**Request Body:**
```json
{
  "auth_code": "string (required)"
}
```

**Example Request:**
```json
{
  "auth_code": "your_linkedin_authorization_code"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Token exchange successful",
  "token_info": {
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9...",
    "expires_in": 3600,
    "token_type": "Bearer"
  }
}
```

### 11. Post to LinkedIn (OAuth)
**POST** `/api/v1/linkedin/post`

Post content to LinkedIn using OAuth tokens.

**Request Body:**
```json
{
  "content": "string (required)",
  "image_path": "string (optional, default: assets/media/image/photo.png)"
}
```

**Example Request:**
```json
{
  "content": "This is a test post using OAuth authentication!",
  "image_path": "https://example.com/image.jpg"
}
```

**Response:**
```json
{
  "success": true,
  "result": {
    "success": true,
    "post_id": "urn:li:activity:123456789",
    "message": "Post published successfully"
  }
}
```

### 12. Automate Content Pipeline
**POST** `/api/v1/automate-content`

Execute the complete content automation pipeline from idea generation to LinkedIn posting.

**Request Body:**
```json
{
  "enable_idea_generation": "boolean (optional, default: true)",
  "enable_content_generation": "boolean (optional, default: true)",
  "enable_image_generation": "boolean (optional, default: true)",
  "enable_posting": "boolean (optional, default: true)",
  "custom_prompt": "string (optional)",
  "style_params": "string (optional)",
  "custom_topic": "string (optional)"
}
```

**Example Request:**
```json
{
  "enable_idea_generation": true,
  "enable_content_generation": true,
  "enable_image_generation": true,
  "enable_posting": true,
  "style_params": "professional and engaging"
}
```

**Complete Example with All Parameters:**
```json
{
  "enable_idea_generation": true,
  "enable_content_generation": true,
  "enable_image_generation": true,
  "enable_posting": true,
  "custom_prompt": "optional custom prompt for idea generation",
  "style_params": "professional and engaging",
  "custom_topic": "optional specific topic instead of AI-generated idea"
}
```

**Response:**
```json
{
  "success": true,
  "pipeline_id": "pipeline_1703123456",
  "stages": {
    "idea_generation": {
      "status": "completed",
      "result": "The hidden costs of ignoring data quality in small business decisions",
      "error": null,
      "duration": 2.5,
      "metadata": {
        "idea_validation": {
          "valid": true,
          "score": 8,
          "feedback": "Score: 8/10 - Excellent topic with strong practical relevance"
        }
      }
    },
    "content_generation": {
      "status": "completed",
      "result": "Generated LinkedIn post content...",
      "error": null,
      "duration": 5.1,
      "metadata": {
        "content_validation": {
          "valid": true,
          "word_count": 245,
          "char_count": 1250
        }
      }
    },
    "image_generation": {
      "status": "completed",
      "result": "generated_images/data_quality_business_1703123456.png",
      "error": null,
      "duration": 12.3
    },
    "linkedin_posting": {
      "status": "completed",
      "result": "urn:li:activity:123456789",
      "error": null,
      "duration": 3.2,
      "metadata": {
        "linkedin_response": {
          "success": true,
          "post_id": "urn:li:activity:123456789"
        }
      }
    }
  },
  "total_duration": 23.1,
  "timestamp": "2024-01-15T10:30:00",
  "final_results": {
    "content": "Generated LinkedIn post content...",
    "image_path": "generated_images/data_quality_business_1703123456.png",
    "post_id": "urn:li:activity:123456789"
  }
}
```

## Complete Usage Examples

### Postman Collection

#### 1. Health Check
```
GET http://127.0.0.1:8001/api/v1/health-check
Headers: Authorization: Bearer your_api_token
```

#### 2. Generate Content
```
POST http://127.0.0.1:8001/api/v1/generate-content
Headers: 
  Authorization: Bearer your_api_token
  Content-Type: application/json
Body:
{
  "topic": "Digital transformation in healthcare",
  "style_params": "professional and informative"
}
```

#### 3. Generate Image
```
POST http://127.0.0.1:8001/api/v1/generate-image
Headers:
  Authorization: Bearer your_api_token
  Content-Type: application/json
Body:
{
  "content_description": "Healthcare professionals using digital technology",
  "style": "modern and professional"
}
```

#### 4. Post to LinkedIn (Legacy)
```
POST http://127.0.0.1:8001/api/v1/post-linkedin
Headers:
  Authorization: Bearer your_api_token
  Content-Type: application/json
Body:
{
  "content": "Your LinkedIn post content here",
  "image": "assets/media/image/photo.png"
}
```

#### 5. Schedule Post
```
POST http://127.0.0.1:8001/api/v1/schedule-post
Headers:
  Authorization: Bearer your_api_token
  Content-Type: application/json
Body:
{
  "datetime": "2024-01-15T14:30:00",
  "content": "Scheduled post content",
  "image": "assets/media/image/photo.png"
}
```

#### 6. Check Status
```
GET http://127.0.0.1:8001/api/v1/status/{job_id}
Headers: Authorization: Bearer your_api_token
```

#### 7. LinkedIn OAuth Authorization
```
GET http://127.0.0.1:8001/api/v1/linkedin/authorize
```

#### 8. LinkedIn OAuth Callback
```
GET http://127.0.0.1:8001/auth_callback?code=your_auth_code&state=your_state
```

#### 9. Save OpenAI API Key
```
POST http://127.0.0.1:8001/api/v1/save-openai-key
Headers:
  Content-Type: application/json
Body:
{
  "api_key": "sk-your-openai-api-key-here"
}
```

#### 10. LinkedIn OAuth Token Exchange (Legacy)
```
POST http://127.0.0.1:8001/api/v1/linkedin/exchange-token
Headers:
  Authorization: Bearer your_api_token
  Content-Type: application/json
Body:
{
  "auth_code": "your_linkedin_authorization_code"
}
```

#### 11. Post to LinkedIn (OAuth)
```
POST http://127.0.0.1:8001/api/v1/linkedin/post
Headers:
  Authorization: Bearer your_api_token
  Content-Type: application/json
Body:
{
  "content": "Your LinkedIn post content",
  "image_path": "https://example.com/image.jpg"
}
```

#### 12. Automate Content Pipeline
```
POST http://127.0.0.1:8001/api/v1/automate-content
Headers:
  Authorization: Bearer your_api_token
  Content-Type: application/json
Body:
{
  "enable_idea_generation": true,
  "enable_content_generation": true,
  "enable_image_generation": true,
  "enable_posting": true,
  "style_params": "professional and engaging"
}
```

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

## Troubleshooting

### Common Errors

#### 1. Missing Required Fields
**Error:** `"Field required"` for `topic`
**Solution:** Ensure you're sending the correct field names:
- For `/api/v1/generate-content`: Use `topic` not `content`
- For `/api/v1/post-linkedin`: Use `content` not `topic`

#### 2. Authentication Errors
**Error:** `401 Unauthorized`
**Solution:** Check that your `BASIC_AUTH_TOKEN` is set correctly and included in the Authorization header.

#### 3. Invalid DateTime Format
**Error:** `"Invalid datetime format"`
**Solution:** Use ISO format: `YYYY-MM-DDTHH:MM:SS`

#### 4. LinkedIn OAuth Errors
**Error:** `"Missing required LinkedIn OAuth environment variables"`
**Solution:** Ensure all LinkedIn OAuth environment variables are set in your `.env` file.

## Features
- ✅ **LinkedIn OAuth Integration** - Secure token management with automated flow
- ✅ **Web-based Authorization** - Simple browser-based OAuth setup
- ✅ **OpenAI API Key Management** - Web interface for API key configuration
- ✅ **Text & Image Posts** - Support for both content types
- ✅ **URL & Local Images** - Upload from web or local files
- ✅ **Automatic Token Refresh** - No manual token management
- ✅ **Content Generation** - AI-powered post creation
- ✅ **Image Generation** - AI-generated visuals with multiple model support
- ✅ **Post Scheduling** - Automated posting with status monitoring

## Notes
- OAuth tokens are automatically stored in `assets/linkedin_tokens.json`
- OpenAI API keys are stored in `.env` file
- Image paths support both local files and public URLs
- All API endpoints require Bearer token authentication (except OAuth flow)
- Web interface available at `http://127.0.0.1:8001` for easy setup
- See `.env.example` for complete configuration 