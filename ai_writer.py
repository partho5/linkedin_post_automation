import logging
from typing import Optional, Dict, Any
import os
import aiofiles
from openai_handler import OpenAIHandler
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class AIWriter:
    def __init__(self):
        try:
            self.openai_handler = OpenAIHandler()
            self.content_tone = os.getenv('CONTENT_TONE', 'professional')
            self.default_style = os.getenv('DEFAULT_STYLE', 'engaging')
            self.prompts_file = 'prompts_linkedin_post.txt'

            logger.info("AI Writer initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize AI Writer: {str(e)}")
            raise

    async def load_prompts(self) -> str:
        """Load LinkedIn post prompts from file"""
        try:
            if os.path.exists(self.prompts_file):
                async with aiofiles.open(self.prompts_file, 'r', encoding='utf-8') as file:
                    content = await file.read()
                    logger.info("Prompts loaded from file successfully")
                    return content
            else:
                logger.warning(f"Prompts file {self.prompts_file} not found, using default")
                return self._get_default_prompt()

        except Exception as e:
            logger.error(f"Failed to load prompts: {str(e)}")
            return self._get_default_prompt()

    def _get_default_prompt(self) -> str:
        """Default LinkedIn post prompt"""
        return """
        Create a professional LinkedIn post that:
        - Is engaging and thought-provoking
        - Uses a professional yet conversational tone
        - Includes relevant hashtags
        - Encourages engagement
        - Is between 100-300 words
        - Has a clear call-to-action
        """

    async def generate_post_content(self, topic: str, style_guide: Optional[str] = None) -> Optional[str]:
        """Generate LinkedIn post content based on topic and style"""
        try:
            base_prompt = await self.load_prompts()

            style = style_guide or self.default_style
            tone = self.content_tone

            full_prompt = f"""
            {base_prompt}

            Topic: {topic}
            Style: {style}
            Tone: {tone}

            Generate a LinkedIn post about the given topic that follows the style and tone requirements.
            Make it authentic, valuable, and engaging for a professional audience.
            """

            content = await self.openai_handler.generate_text(full_prompt)

            if content:
                logger.info(f"Post content generated successfully for topic: {topic}")
                return content
            else:
                logger.error("Failed to generate post content")
                return await self._get_fallback_content(topic)

        except Exception as e:
            logger.error(f"Error generating post content: {str(e)}")
            return await self._get_fallback_content(topic)

    async def analyze_writing_style(self, sample_posts: list) -> Dict[str, Any]:
        """Analyze writing style from sample posts"""
        try:
            if not sample_posts:
                logger.warning("No sample posts provided for style analysis")
                return {"style": "default", "tone": self.content_tone}

            posts_text = "\n---\n".join(sample_posts)

            analysis_prompt = f"""
            Analyze the writing style and tone from these LinkedIn posts:

            {posts_text}

            Provide a detailed analysis of:
            1. Writing style characteristics
            2. Common phrases and patterns
            3. Tone and voice
            4. Hashtag usage patterns
            5. Post structure preferences

            Return the analysis in a structured format.
            """

            analysis = await self.openai_handler.generate_text(analysis_prompt)

            if analysis:
                logger.info("Writing style analysis completed successfully")
                return {
                    "analysis": analysis,
                    "posts_analyzed": len(sample_posts),
                    "status": "success"
                }
            else:
                logger.error("Failed to analyze writing style")
                return {"style": "default", "error": "Analysis failed"}

        except Exception as e:
            logger.error(f"Error analyzing writing style: {str(e)}")
            return {"style": "default", "error": str(e)}

    async def validate_content_quality(self, content: str) -> Dict[str, Any]:
        """Validate generated content quality"""
        try:
            if not content:
                return {"valid": False, "reason": "Content is empty"}

            # Basic validations
            word_count = len(content.split())
            char_count = len(content)

            # LinkedIn post optimal length checks
            if word_count < 10:
                return {"valid": False, "reason": "Content too short"}

            if word_count > 500:
                return {"valid": False, "reason": "Content too long for LinkedIn"}

            if char_count > 3000:  # LinkedIn character limit
                return {"valid": False, "reason": "Exceeds LinkedIn character limit"}

            # Check for professional content
            validation_prompt = f"""
            Evaluate this LinkedIn post for:
            1. Professional appropriateness
            2. Engagement potential
            3. Grammar and clarity
            4. Value to readers

            Post content: {content}

            Provide a score (1-10) and brief feedback.
            """

            validation_result = await self.openai_handler.generate_text(validation_prompt)

            logger.info("Content quality validation completed")

            return {
                "valid": True,
                "word_count": word_count,
                "char_count": char_count,
                "ai_feedback": validation_result,
                "status": "validated"
            }

        except Exception as e:
            logger.error(f"Error validating content quality: {str(e)}")
            return {"valid": False, "reason": f"Validation error: {str(e)}"}

    async def _get_fallback_content(self, topic: str) -> str:
        """Provide fallback content when AI generation fails"""
        fallback_enabled = os.getenv('FALLBACK_ENABLED', 'true').lower() == 'true'

        if fallback_enabled:
            logger.info("Using fallback content generation")
            return f"""
💡 Thoughts on {topic}

In today's rapidly evolving professional landscape, understanding {topic} has become increasingly important.

Key considerations:
• Impact on industry practices
• Future implications
• Actionable insights

What's your experience with {topic}? Share your thoughts below! 👇

#LinkedIn #Professional #Growth #{topic.replace(' ', '')}
            """.strip()
        else:
            logger.error("Fallback disabled and content generation failed")
            return None