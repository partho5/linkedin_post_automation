import logging
from typing import Optional, Dict, Any
import os
from openai_handler import OpenAIHandler
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class ContentIdeaGenerator:
    def __init__(self):
        try:
            self.openai_handler = OpenAIHandler()
            self.default_prompt = self._get_default_idea_prompt()
            self.max_retries = int(os.getenv('MAX_RETRIES', '3'))
            self.retry_delay = int(os.getenv('RETRY_DELAY', '5'))

            logger.info("Content Idea Generator initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize Content Idea Generator: {str(e)}")
            raise

    def _get_default_idea_prompt(self) -> str:
        """Default prompt for generating LinkedIn content ideas"""
        return """You are an expert LinkedIn strategist for a personal brand focused on economics, data analytics, and small economies. 

Generate 1 specific content ideas or post topics that:
- Start with a strong, one-sentence hook
- Solve or reflect on a common problem in data, development, or leadership
- Align with principles like integrity, innovation, and growth mindset
- Include practical insights or relatable anecdotes
- Are relevant to professionals in economics, analytics, or policymaking
- Are optimized for SEO and engagement on LinkedIn

Avoid vague themes—focus on niche, practical, and thought-leader-level insights. Limit to 1000–1300 characters per post when writing.

Return ONLY the topic/title of the content idea, nothing else."""

    async def generate_content_idea(self, custom_prompt: Optional[str] = None) -> Optional[str]:
        """Generate a single content idea for LinkedIn post"""
        try:
            prompt = custom_prompt or self.default_prompt

            for attempt in range(self.max_retries):
                try:
                    idea = await self.openai_handler.generate_text(prompt)
                    
                    if idea:
                        # Clean up the response
                        idea = idea.strip()
                        # Remove any quotes or extra formatting
                        idea = idea.strip('"').strip("'")
                        
                        logger.info(f"Content idea generated successfully: {idea[:50]}...")
                        return idea
                    else:
                        logger.warning(f"Empty response on attempt {attempt + 1}")
                        if attempt < self.max_retries - 1:
                            continue
                        return await self._get_fallback_idea()

                except Exception as e:
                    logger.error(f"Error generating content idea on attempt {attempt + 1}: {str(e)}")
                    if attempt < self.max_retries - 1:
                        continue
                    return await self._get_fallback_idea()

        except Exception as e:
            logger.error(f"Failed to generate content idea: {str(e)}")
            return await self._get_fallback_idea()

    async def generate_multiple_ideas(self, count: int = 3, custom_prompt: Optional[str] = None) -> list:
        """Generate multiple content ideas"""
        try:
            ideas = []
            for i in range(count):
                idea = await self.generate_content_idea(custom_prompt)
                if idea:
                    ideas.append(idea)
            
            logger.info(f"Generated {len(ideas)} content ideas")
            return ideas

        except Exception as e:
            logger.error(f"Failed to generate multiple ideas: {str(e)}")
            return []

    async def validate_idea_quality(self, idea: str) -> Dict[str, Any]:
        """Validate the quality and relevance of a generated idea"""
        try:
            if not idea:
                return {"valid": False, "reason": "Idea is empty"}

            validation_prompt = f"""
            Evaluate this LinkedIn content idea for:
            1. Relevance to economics, data analytics, or small economies
            2. Professional appropriateness
            3. Engagement potential
            4. Originality and thought leadership
            5. Practical value to readers

            Idea: {idea}

            Provide a score (1-10) and brief feedback. Return in format: "Score: X/10 - Feedback: [brief feedback]"
            """

            validation_result = await self.openai_handler.generate_text(validation_prompt)

            # Extract score from response
            score = 5  # Default score
            if validation_result:
                try:
                    if "Score:" in validation_result:
                        score_text = validation_result.split("Score:")[1].split("-")[0].strip()
                        score = int(score_text.split("/")[0])
                except:
                    pass

            is_valid = score >= 6  # Minimum acceptable score

            return {
                "valid": is_valid,
                "score": score,
                "feedback": validation_result,
                "idea": idea
            }

        except Exception as e:
            logger.error(f"Error validating idea quality: {str(e)}")
            return {"valid": False, "reason": f"Validation error: {str(e)}", "idea": idea}

    async def _get_fallback_idea(self) -> str:
        """Provide fallback content idea when generation fails"""
        fallback_ideas = [
            "The hidden costs of ignoring data quality in small business decisions",
            "How microeconomics principles can transform your data strategy",
            "Why small economies are the perfect testing ground for analytics innovation",
            "The surprising connection between behavioral economics and data visualization",
            "How to apply econometric principles to your business analytics"
        ]
        
        import random
        return random.choice(fallback_ideas)

    async def analyze_trending_topics(self) -> Dict[str, Any]:
        """Analyze current trending topics in the field"""
        try:
            trend_prompt = """
            Based on current trends in economics, data analytics, and small economies, 
            identify 3-5 emerging topics that would be valuable for LinkedIn content.
            
            Focus on:
            - Emerging technologies in data science
            - Economic policy changes affecting small businesses
            - New analytical methodologies
            - Industry challenges and solutions
            
            Return as a simple list, one topic per line.
            """

            trends = await self.openai_handler.generate_text(trend_prompt)
            
            if trends:
                trend_list = [t.strip() for t in trends.split('\n') if t.strip()]
                return {
                    "success": True,
                    "trends": trend_list,
                    "count": len(trend_list)
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to generate trending topics"
                }

        except Exception as e:
            logger.error(f"Error analyzing trending topics: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            } 