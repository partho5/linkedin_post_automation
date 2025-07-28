import logging
import os
import asyncio
from typing import Optional, Dict, Any
import httpx
from PIL import Image
import io
from openai_handler import OpenAIHandler
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class ImageHandler:
    def __init__(self):
        try:
            self.openai_handler = OpenAIHandler()
            self.image_size = os.getenv('IMAGE_SIZE', '1024x1024')
            self.image_quality = os.getenv('IMAGE_QUALITY', 'standard')
            self.max_retries = int(os.getenv('MAX_RETRIES', '3'))
            self.retry_delay = int(os.getenv('RETRY_DELAY', '5'))
            self.fallback_enabled = os.getenv('FALLBACK_ENABLED', 'true').lower() == 'true'

            # Create images directory if it doesn't exist
            self.images_dir = 'generated_images'
            os.makedirs(self.images_dir, exist_ok=True)

            logger.info("Image Handler initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize Image Handler: {str(e)}")
            raise

    async def generate_post_image(self, content_summary: str, style: Optional[str] = None) -> Optional[str]:
        """Generate image for LinkedIn post based on content summary"""
        try:
            image_prompt = await self._create_image_prompt(content_summary, style)

            if not image_prompt:
                logger.error("Failed to create image prompt")
                return await self._get_fallback_image() if self.fallback_enabled else None
            else:
                print(f"image_prompt={image_prompt}")

            # Generate image using OpenAI (returns base64 data or URL based on model)
            image_result = await self.openai_handler.generate_image(image_prompt)

            if image_result:
                # Check if result is base64 data or URL
                if isinstance(image_result, str) and image_result.startswith('data:image') or len(image_result) > 1000:
                    # Likely base64 data
                    local_path = await self._save_base64_image(image_result, content_summary)
                else:
                    # Likely URL, use download method
                    local_path = await self._download_and_save_image(image_result, content_summary)
                
                logger.info(f"Image generated and saved successfully: {local_path}")
                return local_path
            else:
                logger.error("Failed to generate image via OpenAI")
                return await self._get_fallback_image() if self.fallback_enabled else None

        except Exception as e:
            logger.error(f"Error generating post image: {str(e)}")
            return await self._get_fallback_image() if self.fallback_enabled else None

    async def _create_image_prompt(self, content_summary: str, style: Optional[str] = None) -> Optional[str]:
        """Create optimized image prompt for LinkedIn posts"""
        try:
            style = style or "professional business"

            prompt_template = f"""
            Create a professional, LinkedIn-appropriate image for a post about: {content_summary}

            Style: {style}

            Guidelines:
            - The image should metaphorically represent the post’s concept, without literal or keyword-based illustrations.
            """

            # Use AI to refine the prompt for better image generation
            refined_prompt = await self.openai_handler.generate_text(
                f"Convert this into a concise, effective DALL-E prompt (max 400 chars): {prompt_template}"
            )

            final_prompt = refined_prompt if refined_prompt else prompt_template
            final_prompt += """
             The image must contain a maximum of 1 to 3 objects. Having more than 3 objects in the image is not allowed.
            - for human, face MUST be photorealistic, camera-captured look.
            - Important constraint: You must strictly avoid all cliché imagery such as light bulbs, gear icons, graphs, charts, digital dashboards, or generic technology symbols.
            - Use only real-world, everyday objects commonly seen in natural or human environments — nothing abstract, symbolic, or icon-based.
            - No small objects, icons, or decorative elements should surround or distract from the main subject.
            - Focus on a single, clear composition with minimal or no background clutter.
            - Do not include any text or overlays.
            """

            logger.info("Image prompt created successfully")
            return final_prompt

        except Exception as e:
            logger.error(f"Error creating image prompt: {str(e)}")
            return None

    async def _download_and_save_image2(self, image_url: str, content_summary: str) -> Optional[str]:
        """Download image from URL and save locally"""
        try:
            # Create safe filename from content summary
            safe_filename = "".join(c for c in content_summary[:50] if c.isalnum() or c in (' ', '-', '_')).rstrip()
            safe_filename = safe_filename.replace(' ', '_')
            timestamp = str(int(asyncio.get_event_loop().time()))
            filename = f"{safe_filename}_{timestamp}.png"
            file_path = os.path.join(self.images_dir, filename)

            # Special handling for DALL-E URLs
            headers = {}
            if 'oaidalleapiprodscus.blob.core.windows.net' in image_url:
                # DALL-E URLs are temporary and may need special handling
                # Try with different timeout and retry logic
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }

            async with httpx.AsyncClient(timeout=60.0) as client:
                for attempt in range(3):
                    try:
                        response = await client.get(image_url, headers=headers)
                        response.raise_for_status()

                        # Save the image
                        with open(file_path, 'wb') as f:
                            f.write(response.content)

                        # Optimize image size if needed
                        await self._optimize_image(file_path)

                        logger.info(f"Image downloaded and saved: {file_path}")
                        return file_path
                        
                    except httpx.HTTPStatusError as e:
                        if e.response.status_code == 403 and attempt < 2:
                            logger.warning(f"403 error on attempt {attempt + 1}, retrying...")
                            await asyncio.sleep(2 ** attempt)  # Exponential backoff
                            continue
                        else:
                            raise
                    except Exception as e:
                        if attempt < 2:
                            logger.warning(f"Download error on attempt {attempt + 1}, retrying...")
                            await asyncio.sleep(2 ** attempt)
                            continue
                        else:
                            raise

        except Exception as e:
            logger.error(f"Error downloading image: {str(e)}")
            return None

    async def _save_base64_image(self, base64_data: str, content_summary: str) -> Optional[str]:
        """Save base64 image data directly to local file"""
        try:
            import base64
            
            # Create safe filename from content summary
            safe_filename = "".join(c for c in content_summary[:50] if c.isalnum() or c in (' ', '-', '_')).rstrip()
            safe_filename = safe_filename.replace(' ', '_')
            timestamp = str(int(asyncio.get_event_loop().time()))
            filename = f"{safe_filename}_{timestamp}.png"
            file_path = os.path.join(self.images_dir, filename)

            # Decode base64 data and save to file
            image_bytes = base64.b64decode(base64_data)
            
            with open(file_path, 'wb') as f:
                f.write(image_bytes)

            # Optimize image size if needed
            await self._optimize_image(file_path)

            logger.info(f"Base64 image saved: {file_path}")
            return file_path

        except Exception as e:
            logger.error(f"Error saving base64 image: {str(e)}")
            return None

    async def _optimize_image(self, file_path: str) -> None:
        """Optimize image for LinkedIn posting"""
        try:
            with Image.open(file_path) as img:
                # LinkedIn optimal dimensions: 1200x627 for shared content
                # Keep original if it's already optimal
                width, height = img.size

                # Only resize if image is significantly larger
                if width > 1920 or height > 1080:
                    # Calculate new dimensions maintaining aspect ratio
                    if width > height:
                        new_width = 1200
                        new_height = int((height * 1200) / width)
                    else:
                        new_height = 1080
                        new_width = int((width * 1080) / height)

                    img_resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                    img_resized.save(file_path, optimize=True, quality=85)
                    logger.info(f"Image optimized: {width}x{height} -> {new_width}x{new_height}")

        except Exception as e:
            logger.error(f"Error optimizing image: {str(e)}")

    async def _get_fallback_image(self) -> Optional[str]:
        """Generate or return fallback image when main generation fails"""
        try:
            if not self.fallback_enabled:
                return None

            fallback_prompts = [
                "Professional business background with abstract geometric shapes, corporate blue colors",
                "Clean minimalist design with soft gradients, suitable for LinkedIn business content",
                "Professional workspace aesthetic with modern design elements, neutral colors"
            ]

            for prompt in fallback_prompts:
                try:
                    image_result = await self.openai_handler.generate_image(prompt)
                    if image_result:
                        # Check if result is base64 data or URL
                        if isinstance(image_result, str) and image_result.startswith('data:image') or len(image_result) > 1000:
                            # Likely base64 data
                            file_path = await self._save_base64_image(image_result, "fallback")
                        else:
                            # Likely URL, use download method
                            file_path = await self._download_and_save_image(image_result, "fallback")
                        
                        logger.info("Fallback image generated successfully")
                        return file_path
                except Exception as e:
                    logger.warning(f"Fallback attempt failed: {str(e)}")
                    continue

            logger.error("All fallback image generation attempts failed")
            return None

        except Exception as e:
            logger.error(f"Error in fallback image generation: {str(e)}")
            return None

    async def process_image_specs(self, content: str, custom_specs: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Process and validate image specifications"""
        try:
            specs = {
                "size": custom_specs.get("size", self.image_size) if custom_specs else self.image_size,
                "quality": custom_specs.get("quality", self.image_quality) if custom_specs else self.image_quality,
                "style": custom_specs.get("style", "professional") if custom_specs else "professional",
                "content_theme": content[:100] + "..." if len(content) > 100 else content
            }

            # Validate size format
            if not self._validate_image_size(specs["size"]):
                specs["size"] = "1024x1024"
                logger.warning(f"Invalid image size, using default: {specs['size']}")

            logger.info("Image specifications processed successfully")
            return specs

        except Exception as e:
            logger.error(f"Error processing image specs: {str(e)}")
            return {
                "size": "1024x1024",
                "quality": "standard",
                "style": "professional",
                "content_theme": "default"
            }

    def _validate_image_size(self, size: str) -> bool:
        """Validate image size format"""
        try:
            valid_sizes = ["256x256", "512x512", "1024x1024", "1792x1024", "1024x1792"]
            return size in valid_sizes
        except Exception:
            return False

    async def cleanup_old_images(self, max_age_days: int = 7) -> Dict[str, Any]:
        """Clean up old generated images"""
        try:
            import time
            current_time = time.time()
            max_age_seconds = max_age_days * 24 * 60 * 60

            deleted_count = 0
            total_size_freed = 0

            for filename in os.listdir(self.images_dir):
                file_path = os.path.join(self.images_dir, filename)
                if os.path.isfile(file_path):
                    file_age = current_time - os.path.getctime(file_path)
                    if file_age > max_age_seconds:
                        file_size = os.path.getsize(file_path)
                        os.remove(file_path)
                        deleted_count += 1
                        total_size_freed += file_size

            logger.info(
                f"Cleanup completed: {deleted_count} files deleted, {total_size_freed / 1024 / 1024:.2f} MB freed")

            return {
                "deleted_files": deleted_count,
                "size_freed_mb": total_size_freed / 1024 / 1024,
                "status": "completed"
            }

        except Exception as e:
            logger.error(f"Error during image cleanup: {str(e)}")
            return {"status": "failed", "error": str(e)}