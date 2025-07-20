import logging
import os
import asyncio
from typing import Optional, Dict, Any
import httpx
import json
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class LinkedInAPI:
    def __init__(self, oauth_handler=None):
        try:
            self.oauth_handler = oauth_handler
            self.access_token = os.getenv('LINKEDIN_ACCESS_TOKEN')
            if not self.access_token:
                logger.warning("LINKEDIN_ACCESS_TOKEN not found in environment variables")

            self.base_url = "https://api.linkedin.com/v2"
            self.max_retries = int(os.getenv('MAX_RETRIES', '3'))
            self.retry_delay = int(os.getenv('RETRY_DELAY', '5'))

            # LinkedIn API endpoints
            self.endpoints = {
                'profile': f"{self.base_url}/people/~",
                'shares': f"{self.base_url}/shares",
                'assets': f"{self.base_url}/assets?action=registerUpload"
            }

            logger.info("LinkedIn API Handler initialized")

        except Exception as e:
            logger.error(f"Failed to initialize LinkedIn API Handler: {str(e)}")
            raise

    async def _get_access_token(self) -> Optional[str]:
        """Get access token from OAuth handler if available, otherwise use environment variable"""
        if self.oauth_handler:
            try:
                return await self.oauth_handler.get_valid_access_token()
            except Exception as e:
                logger.warning(f"Failed to get token from OAuth handler: {str(e)}")
        return self.access_token

    async def validate_credentials(self) -> Dict[str, Any]:
        """Validate LinkedIn API credentials"""
        try:
            access_token = await self._get_access_token()
            if not access_token:
                return {
                    "valid": False,
                    "error": "Access token not configured",
                    "status": "missing_token"
                }

            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(self.endpoints['profile'], headers=headers)

                if response.status_code == 200:
                    profile_data = response.json()
                    logger.info("LinkedIn credentials validated successfully")
                    return {
                        "valid": True,
                        "status": "authenticated",
                        "profile_id": profile_data.get('id'),
                        "first_name": profile_data.get('localizedFirstName'),
                        "last_name": profile_data.get('localizedLastName')
                    }
                else:
                    logger.error(f"LinkedIn credential validation failed: {response.status_code}")
                    return {
                        "valid": False,
                        "error": f"API returned status {response.status_code}",
                        "status": "invalid_token"
                    }

        except Exception as e:
            logger.error(f"Error validating LinkedIn credentials: {str(e)}")
            return {
                "valid": False,
                "error": str(e),
                "status": "validation_error"
            }

    async def _get_user_id(self, access_token: str) -> Optional[str]:
        """Get user ID from LinkedIn userinfo endpoint"""
        try:
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get("https://api.linkedin.com/v2/userinfo", headers=headers)
                
                if response.status_code == 200:
                    user_data = response.json()
                    user_id = user_data.get('sub')
                    logger.info(f"User ID retrieved: {user_id}")
                    return user_id
                else:
                    logger.error(f"Failed to get user info: {response.status_code}")
                    return None

        except Exception as e:
            logger.error(f"Error getting user ID: {str(e)}")
            return None

    async def _register_image_upload(self, access_token: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Register image upload with LinkedIn"""
        try:
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }

            payload = {
                "registerUploadRequest": {
                    "recipes": ["urn:li:digitalmediaRecipe:feedshare-image"],
                    "owner": f"urn:li:person:{user_id}",
                    "serviceRelationships": [
                        {
                            "relationshipType": "OWNER",
                            "identifier": "urn:li:userGeneratedContent"
                        }
                    ]
                }
            }

            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    "https://api.linkedin.com/v2/assets?action=registerUpload",
                    headers=headers,
                    json=payload
                )

                if response.status_code == 200:
                    upload_data = response.json()
                    logger.info("Image upload registered successfully")
                    return upload_data
                else:
                    logger.error(f"Failed to register upload: {response.status_code}")
                    return None

        except Exception as e:
            logger.error(f"Error registering image upload: {str(e)}")
            return None

    async def _upload_image_binary(self, upload_url: str, access_token: str, image_data: bytes) -> bool:
        """Upload image binary data to LinkedIn"""
        try:
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "image/png"
            }

            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.put(upload_url, content=image_data, headers=headers)

                if response.status_code == 201:
                    logger.info("Image uploaded successfully")
                    return True
                else:
                    logger.error(f"Failed to upload image: {response.status_code}")
                    return False

        except Exception as e:
            logger.error(f"Error uploading image: {str(e)}")
            return False

    async def _create_post_with_image(self, access_token: str, user_id: str, text: str, asset_urn: str) -> Dict[str, Any]:
        """Create LinkedIn post with image using exact API specification"""
        try:
            headers = {
                "Authorization": f"Bearer {access_token}",
                "X-Restli-Protocol-Version": "2.0.0",
                "Content-Type": "application/json"
            }

            payload = {
                "author": f"urn:li:person:{user_id}",
                "lifecycleState": "PUBLISHED",
                "specificContent": {
                    "com.linkedin.ugc.ShareContent": {
                        "shareCommentary": {
                            "text": text
                        },
                        "shareMediaCategory": "IMAGE",
                        "media": [
                            {
                                "status": "READY",
                                "description": {
                                    "text": "Generated image for LinkedIn post"
                                },
                                "media": asset_urn,
                                "title": {
                                    "text": "LinkedIn Post Image"
                                }
                            }
                        ]
                    }
                },
                "visibility": {
                    "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
                }
            }

            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    "https://api.linkedin.com/v2/ugcPosts",
                    headers=headers,
                    json=payload
                )

                if response.status_code == 201:
                    post_data = response.json()
                    logger.info("Post created successfully")
                    return {
                        "success": True,
                        "post_id": post_data.get("id"),
                        "status": "posted",
                        "response": post_data
                    }
                else:
                    error_msg = f"LinkedIn API returned status {response.status_code}: {response.text}"
                    logger.error(error_msg)
                    return {
                        "success": False,
                        "error": error_msg,
                        "status": "api_error",
                        "status_code": response.status_code
                    }

        except Exception as e:
            logger.error(f"Error creating post: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "status": "post_error"
            }

    async def post_content(self, text: str, image_path: Optional[str] = None) -> Dict[str, Any]:
        """Post content to LinkedIn following exact 6-step sequence"""
        try:
            access_token = await self._get_access_token()
            if not access_token:
                return {
                    "success": False,
                    "error": "LinkedIn access token not configured",
                    "status": "missing_credentials"
                }

            # Step 3: Get user ID from userinfo endpoint
            user_id = await self._get_user_id(access_token)
            if not user_id:
                return {
                    "success": False,
                    "error": "Failed to get user ID",
                    "status": "user_id_error"
                }

            # Step 4: Register image upload (if image provided)
            asset_urn = None
            if image_path:
                upload_data = await self._register_image_upload(access_token, user_id)
                if not upload_data:
                    return {
                        "success": False,
                        "error": "Failed to register image upload",
                        "status": "upload_registration_error"
                    }

                asset_urn = upload_data['value']['asset']
                upload_url = upload_data['value']['uploadMechanism']['com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest']['uploadUrl']

                # Step 5: Upload image binary data
                image_data = await self._get_image_data(image_path)
                if not image_data:
                    return {
                        "success": False,
                        "error": "Failed to read image data",
                        "status": "image_read_error"
                    }

                upload_success = await self._upload_image_binary(upload_url, access_token, image_data)
                if not upload_success:
                    return {
                        "success": False,
                        "error": "Failed to upload image",
                        "status": "image_upload_error"
                    }

            # Step 6: Create post
            if asset_urn:
                result = await self._create_post_with_image(access_token, user_id, text, asset_urn)
            else:
                # Text-only post
                result = await self._create_text_post(access_token, user_id, text)

            return result

        except Exception as e:
            logger.error(f"Error posting to LinkedIn: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "status": "post_error"
            }

    async def _get_image_data(self, image_path: str) -> Optional[bytes]:
        """Get image data as bytes from local file or URL"""
        try:
            if image_path.startswith(('http://', 'https://')):
                # Download from URL
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.get(image_path)
                    if response.status_code == 200:
                        return response.content
                    else:
                        logger.error(f"Failed to download image: {response.status_code}")
                        return None
            else:
                # Read local file
                if os.path.exists(image_path):
                    with open(image_path, 'rb') as f:
                        return f.read()
                else:
                    logger.error(f"Image file not found: {image_path}")
                    return None

        except Exception as e:
            logger.error(f"Error getting image data: {str(e)}")
            return None

    async def _create_text_post(self, access_token: str, user_id: str, text: str) -> Dict[str, Any]:
        """Create text-only LinkedIn post"""
        try:
            headers = {
                "Authorization": f"Bearer {access_token}",
                "X-Restli-Protocol-Version": "2.0.0",
                "Content-Type": "application/json"
            }

            payload = {
                "author": f"urn:li:person:{user_id}",
                "lifecycleState": "PUBLISHED",
                "specificContent": {
                    "com.linkedin.ugc.ShareContent": {
                        "shareCommentary": {
                            "text": text
                        },
                        "shareMediaCategory": "NONE"
                    }
                },
                "visibility": {
                    "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
                }
            }

            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    "https://api.linkedin.com/v2/ugcPosts",
                    headers=headers,
                    json=payload
                )

                if response.status_code == 201:
                    post_data = response.json()
                    logger.info("Text post created successfully")
                    return {
                        "success": True,
                        "post_id": post_data.get("id"),
                        "status": "posted",
                        "response": post_data
                    }
                else:
                    error_msg = f"LinkedIn API returned status {response.status_code}: {response.text}"
                    logger.error(error_msg)
                    return {
                        "success": False,
                        "error": error_msg,
                        "status": "api_error",
                        "status_code": response.status_code
                    }

        except Exception as e:
            logger.error(f"Error creating text post: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "status": "post_error"
            }

    async def _get_profile_id(self) -> Optional[str]:
        """Get the LinkedIn profile ID"""
        try:
            validation_result = await self.validate_credentials()
            return validation_result.get("profile_id") if validation_result.get("valid") else None
        except Exception as e:
            logger.error(f"Error getting profile ID: {str(e)}")
            return None

    async def handle_posting_errors(self, error_response: Dict[str, Any]) -> Dict[str, Any]:
        """Handle and categorize LinkedIn posting errors"""
        try:
            status_code = error_response.get("status_code", 0)
            error_msg = error_response.get("error", "Unknown error")

            error_categories = {
                400: "Bad Request - Check post content and format",
                401: "Unauthorized - Invalid or expired access token",
                403: "Forbidden - Insufficient permissions",
                404: "Not Found - Invalid endpoint or resource",
                422: "Unprocessable Entity - Content policy violation",
                429: "Rate Limited - Too many requests",
                500: "Internal Server Error - LinkedIn API issue"
            }

            category = error_categories.get(status_code, "Unknown Error")

            logger.error(f"LinkedIn posting error: {category} - {error_msg}")

            return {
                "error_category": category,
                "status_code": status_code,
                "original_error": error_msg,
                "recommended_action": await self._get_error_recommendation(status_code),
                "retry_recommended": status_code in [429, 500, 502, 503, 504]
            }

        except Exception as e:
            logger.error(f"Error handling posting errors: {str(e)}")
            return {
                "error_category": "Error Handler Failed",
                "original_error": str(e),
                "retry_recommended": False
            }

    async def _get_error_recommendation(self, status_code: int) -> str:
        """Get recommendation for handling specific error codes"""
        recommendations = {
            400: "Review post content format and LinkedIn API requirements",
            401: "Refresh or regenerate LinkedIn access token",
            403: "Check LinkedIn app permissions and user authorization",
            404: "Verify API endpoints and user profile accessibility",
            422: "Review content for policy violations or inappropriate material",
            429: "Implement exponential backoff and reduce request frequency",
            500: "Wait and retry, LinkedIn API may be experiencing issues"
        }

        return recommendations.get(status_code, "Contact LinkedIn API support for assistance")

    async def get_post_analytics(self, post_id: str) -> Dict[str, Any]:
        """Get analytics for a posted LinkedIn content (if available)"""
        try:
            if not post_id:
                return {"error": "Post ID required for analytics"}

            # Note: LinkedIn analytics require additional permissions
            # This is a placeholder for future implementation
            logger.info(f"Analytics requested for post: {post_id}")

            return {
                "post_id": post_id,
                "status": "analytics_not_implemented",
                "message": "Analytics feature requires additional LinkedIn permissions"
            }

        except Exception as e:
            logger.error(f"Error getting post analytics: {str(e)}")
            return {"error": str(e), "status": "analytics_error"}