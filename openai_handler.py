import asyncio
import logging
from typing import Optional, Dict, Any
import openai
from openai import AsyncOpenAI
import os
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class OpenAIHandler:
    def __init__(self):
        try:
            self.api_key = os.getenv('OPENAI_API_KEY')
            if not self.api_key:
                raise ValueError("OPENAI_API_KEY not found in environment variables")

            self.client = AsyncOpenAI(api_key=self.api_key)
            self.text_model = os.getenv('TEXT_MODEL', 'gpt-4-turbo-preview')
            self.image_model = os.getenv('IMAGE_MODEL', 'dall-e-2')  # Use cheaper model by default
            self.max_retries = int(os.getenv('MAX_RETRIES', '3'))
            self.retry_delay = int(os.getenv('RETRY_DELAY', '5'))

            logger.info("OpenAI Handler initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize OpenAI Handler: {str(e)}")
            raise

    async def generate_text(self, prompt: str, model: Optional[str] = None) -> Optional[str]:
        """Generate text content using OpenAI API"""
        try:
            model_to_use = model or self.text_model

            for attempt in range(self.max_retries):
                try:
                    response = await self.client.chat.completions.create(
                        model=model_to_use,
                        messages=[
                            {"role": "system", "content": "You are a professional LinkedIn content creator."},
                            {"role": "user", "content": prompt}
                        ],
                        max_tokens=1000,
                        temperature=0.7
                    )

                    content = response.choices[0].message.content
                    logger.info(f"Text generated successfully with model: {model_to_use}")
                    return content.strip()

                except openai.RateLimitError as e:
                    logger.warning(f"Rate limit hit on attempt {attempt + 1}: {str(e)}")
                    if attempt < self.max_retries - 1:
                        await asyncio.sleep(self.retry_delay * (attempt + 1))
                        continue
                    raise

                except openai.APIError as e:
                    logger.error(f"OpenAI API error on attempt {attempt + 1}: {str(e)}")
                    if attempt < self.max_retries - 1:
                        await asyncio.sleep(self.retry_delay)
                        continue
                    raise

        except Exception as e:
            logger.error(f"Failed to generate text: {str(e)}")
            return None

    async def generate_image(self, prompt: str, model: Optional[str] = None) -> Optional[str]:
        """Generate image using DALL-E API"""
        try:
            model_to_use = model or self.image_model
            image_size = os.getenv('IMAGE_SIZE', '1024x1024')
            image_quality = os.getenv('IMAGE_QUALITY', 'standard')

            for attempt in range(self.max_retries):
                try:
                    # Prepare parameters
                    params = {
                        "model": model_to_use,
                        "prompt": prompt,
                        "size": image_size,
                        "n": 1,
                        "response_format": "b64_json"  # Get base64 data instead of URL
                    }
                    
                    # Only add quality parameter for dall-e-3
                    if model_to_use == "dall-e-3":
                        params["quality"] = image_quality

                    response = await self.client.images.generate(**params)

                    # Return base64 data instead of URL
                    image_data = response.data[0].b64_json
                    logger.info(f"Image generated successfully with model: {model_to_use}")
                    return image_data

                except openai.RateLimitError as e:
                    logger.warning(f"Rate limit hit on attempt {attempt + 1}: {str(e)}")
                    if attempt < self.max_retries - 1:
                        await asyncio.sleep(self.retry_delay * (attempt + 1))
                        continue
                    raise

                except openai.APIError as e:
                    logger.error(f"OpenAI API error on attempt {attempt + 1}: {str(e)}")
                    if attempt < self.max_retries - 1:
                        await asyncio.sleep(self.retry_delay)
                        continue
                    raise

        except Exception as e:
            logger.error(f"Failed to generate image: {str(e)}")
            return None

    async def health_check(self) -> Dict[str, Any]:
        """Check OpenAI API health"""
        try:
            response = await self.client.chat.completions.create(
                model=self.text_model,
                messages=[{"role": "user", "content": "Hi"}],
                max_tokens=10
            )

            return {
                "status": "healthy",
                "model": self.text_model,
                "api_responsive": True
            }

        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "api_responsive": False
            }