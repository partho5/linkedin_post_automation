import logging
import asyncio
from typing import Optional, Dict, Any, List
from datetime import datetime
import time
from dataclasses import dataclass
from enum import Enum

from content_idea_generator import ContentIdeaGenerator
from ai_writer import AIWriter
from image_generation_handler import ImageHandler
from linkedin_api_handler import LinkedInAPI

logger = logging.getLogger(__name__)


class PipelineStage(Enum):
    IDEA_GENERATION = "idea_generation"
    CONTENT_GENERATION = "content_generation"
    IMAGE_GENERATION = "image_generation"
    LINKEDIN_POSTING = "linkedin_posting"


class StageStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class StageResult:
    stage: PipelineStage
    status: StageStatus
    result: Optional[str] = None
    error: Optional[str] = None
    duration: float = 0.0
    metadata: Optional[Dict[str, Any]] = None


class ContentAutomationPipeline:
    def __init__(self):
        try:
            self.idea_generator = ContentIdeaGenerator()
            self.ai_writer = AIWriter()
            self.image_handler = ImageHandler()
            
            # Initialize LinkedIn API with OAuth handler if credentials are available
            try:
                from linkedin_oauth_handler import LinkedInOAuthHandler
                import os
                
                client_id = os.getenv('LINKEDIN_CLIENT_ID')
                client_secret = os.getenv('LINKEDIN_CLIENT_SECRET')
                redirect_uri = os.getenv('LINKEDIN_CALLBACK_URL')
                
                if all([client_id, client_secret, redirect_uri]):
                    oauth_handler = LinkedInOAuthHandler(
                        client_id=client_id,
                        client_secret=client_secret,
                        redirect_uri=redirect_uri
                    )
                    self.linkedin_api = LinkedInAPI(oauth_handler=oauth_handler)
                    logger.info("LinkedIn API initialized with OAuth handler")
                else:
                    self.linkedin_api = LinkedInAPI()
                    logger.warning("LinkedIn OAuth credentials not found, using legacy token method")
            except Exception as e:
                self.linkedin_api = LinkedInAPI()
                logger.warning(f"Failed to initialize OAuth handler: {str(e)}, using legacy token method")
            
            logger.info("Content Automation Pipeline initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize Content Automation Pipeline: {str(e)}")
            raise

    async def execute_full_pipeline(
        self,
        enable_idea_generation: bool = True,
        enable_content_generation: bool = True,
        enable_image_generation: bool = True,
        enable_posting: bool = True,
        custom_prompt: Optional[str] = None,
        style_params: Optional[str] = None,
        custom_topic: Optional[str] = None
    ) -> Dict[str, Any]:
        """Execute the complete content automation pipeline"""
        
        pipeline_start_time = time.time()
        pipeline_id = f"pipeline_{int(pipeline_start_time)}"
        
        logger.info(f"Starting pipeline execution: {pipeline_id}")
        
        stages = {}
        current_topic = None
        current_content = None
        current_image = None
        
        try:
            # Stage 1: Idea Generation
            if enable_idea_generation:
                logger.info("Starting idea generation stage")
                idea_result = await self._execute_idea_generation(custom_prompt, custom_topic)
                stages[PipelineStage.IDEA_GENERATION] = idea_result
                current_topic = idea_result.result
                
                if idea_result.status == StageStatus.FAILED:
                    logger.error(f"Idea generation failed: {idea_result.error}")
                    return self._create_pipeline_response(
                        pipeline_id, stages, pipeline_start_time, success=False, error=idea_result.error
                    )
            else:
                current_topic = custom_topic or "Default topic"
                stages[PipelineStage.IDEA_GENERATION] = StageResult(
                    stage=PipelineStage.IDEA_GENERATION,
                    status=StageStatus.SKIPPED,
                    result=current_topic
                )

            # Stage 2: Content Generation
            if enable_content_generation:
                logger.info("Starting content generation stage")
                content_result = await self._execute_content_generation(current_topic, style_params)
                stages[PipelineStage.CONTENT_GENERATION] = content_result
                current_content = content_result.result
                
                if content_result.status == StageStatus.FAILED:
                    logger.error(f"Content generation failed: {content_result.error}")
                    return self._create_pipeline_response(
                        pipeline_id, stages, pipeline_start_time, success=False, error=content_result.error
                    )
            else:
                current_content = "Default content"
                stages[PipelineStage.CONTENT_GENERATION] = StageResult(
                    stage=PipelineStage.CONTENT_GENERATION,
                    status=StageStatus.SKIPPED,
                    result=current_content
                )

            # Stage 3: Image Generation
            if enable_image_generation:
                logger.info("Starting image generation stage")
                image_result = await self._execute_image_generation(current_content, style_params)
                stages[PipelineStage.IMAGE_GENERATION] = image_result
                current_image = image_result.result
                
                if image_result.status == StageStatus.FAILED:
                    logger.warning(f"Image generation failed: {image_result.error}, continuing without image")
                    current_image = None
            else:
                current_image = None
                stages[PipelineStage.IMAGE_GENERATION] = StageResult(
                    stage=PipelineStage.IMAGE_GENERATION,
                    status=StageStatus.SKIPPED
                )

            # Stage 4: LinkedIn Posting
            if enable_posting:
                logger.info("Starting LinkedIn posting stage")
                posting_result = await self._execute_linkedin_posting(current_content, current_image)
                stages[PipelineStage.LINKEDIN_POSTING] = posting_result
                
                if posting_result.status == StageStatus.FAILED:
                    logger.error(f"LinkedIn posting failed: {posting_result.error}")
                    return self._create_pipeline_response(
                        pipeline_id, stages, pipeline_start_time, success=False, error=posting_result.error
                    )
            else:
                stages[PipelineStage.LINKEDIN_POSTING] = StageResult(
                    stage=PipelineStage.LINKEDIN_POSTING,
                    status=StageStatus.SKIPPED
                )

            # Pipeline completed successfully
            total_duration = time.time() - pipeline_start_time
            logger.info(f"Pipeline completed successfully in {total_duration:.2f} seconds")
            
            return self._create_pipeline_response(
                pipeline_id, stages, pipeline_start_time, success=True
            )

        except Exception as e:
            logger.error(f"Pipeline execution failed: {str(e)}")
            return self._create_pipeline_response(
                pipeline_id, stages, pipeline_start_time, success=False, error=str(e)
            )

    async def _execute_idea_generation(self, custom_prompt: Optional[str], custom_topic: Optional[str]) -> StageResult:
        """Execute idea generation stage"""
        start_time = time.time()
        
        try:
            if custom_topic:
                # Use provided topic
                idea = custom_topic
                status = StageStatus.COMPLETED
                error = None
            else:
                # Generate new idea
                idea = await self.idea_generator.generate_content_idea(custom_prompt)
                if idea:
                    # Validate idea quality
                    validation = await self.idea_generator.validate_idea_quality(idea)
                    if validation.get("valid", False):
                        status = StageStatus.COMPLETED
                        error = None
                    else:
                        status = StageStatus.FAILED
                        error = f"Idea validation failed: {validation.get('feedback', 'Unknown error')}"
                else:
                    status = StageStatus.FAILED
                    error = "Failed to generate content idea"

            duration = time.time() - start_time
            
            return StageResult(
                stage=PipelineStage.IDEA_GENERATION,
                status=status,
                result=idea,
                error=error,
                duration=duration,
                metadata={"idea_validation": validation if 'validation' in locals() else None}
            )

        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Idea generation error: {str(e)}")
            return StageResult(
                stage=PipelineStage.IDEA_GENERATION,
                status=StageStatus.FAILED,
                error=str(e),
                duration=duration
            )

    async def _execute_content_generation(self, topic: str, style_params: Optional[str]) -> StageResult:
        """Execute content generation stage"""
        start_time = time.time()
        
        try:
            content = await self.ai_writer.generate_post_content(topic, style_params)
            
            if content:
                # Validate content quality
                validation = await self.ai_writer.validate_content_quality(content)
                if validation.get("valid", False):
                    status = StageStatus.COMPLETED
                    error = None
                else:
                    status = StageStatus.FAILED
                    error = f"Content validation failed: {validation.get('reason', 'Unknown error')}"
            else:
                status = StageStatus.FAILED
                error = "Failed to generate content"

            duration = time.time() - start_time
            
            return StageResult(
                stage=PipelineStage.CONTENT_GENERATION,
                status=status,
                result=content,
                error=error,
                duration=duration,
                metadata={"content_validation": validation if 'validation' in locals() else None}
            )

        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Content generation error: {str(e)}")
            return StageResult(
                stage=PipelineStage.CONTENT_GENERATION,
                status=StageStatus.FAILED,
                error=str(e),
                duration=duration
            )

    async def _execute_image_generation(self, content: str, style_params: Optional[str]) -> StageResult:
        """Execute image generation stage"""
        start_time = time.time()
        
        try:
            # Create image description from content
            image_description = await self._create_image_description_from_content(content)
            
            image_path = await self.image_handler.generate_post_image(image_description, style_params)
            
            if image_path:
                status = StageStatus.COMPLETED
                error = None
            else:
                status = StageStatus.FAILED
                error = "Failed to generate image"

            duration = time.time() - start_time
            
            return StageResult(
                stage=PipelineStage.IMAGE_GENERATION,
                status=status,
                result=image_path,
                error=error,
                duration=duration
            )

        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Image generation error: {str(e)}")
            return StageResult(
                stage=PipelineStage.IMAGE_GENERATION,
                status=StageStatus.FAILED,
                error=str(e),
                duration=duration
            )

    async def _execute_linkedin_posting(self, content: str, image_path: Optional[str]) -> StageResult:
        """Execute LinkedIn posting stage"""
        start_time = time.time()
        
        try:
            result = await self.linkedin_api.post_content(content, image_path)
            
            if result.get("success", False):
                status = StageStatus.COMPLETED
                error = None
                post_id = result.get("post_id")
            else:
                status = StageStatus.FAILED
                error = result.get("error", "Unknown posting error")
                post_id = None

            duration = time.time() - start_time
            
            return StageResult(
                stage=PipelineStage.LINKEDIN_POSTING,
                status=status,
                result=post_id,
                error=error,
                duration=duration,
                metadata={"linkedin_response": result}
            )

        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"LinkedIn posting error: {str(e)}")
            return StageResult(
                stage=PipelineStage.LINKEDIN_POSTING,
                status=StageStatus.FAILED,
                error=str(e),
                duration=duration
            )

    async def _create_image_description_from_content(self, content: str) -> str:
        """Create image description from content for image generation"""
        try:
            # Extract key themes from content for image generation
            description_prompt = f"""
            Extract the main visual theme or concept from this LinkedIn post content to create an image prompt.
            Focus on the core message, key visual elements, and professional context.
            
            Content: {content}
            
            Return a concise image description (max 100 words) suitable for DALL-E image generation.
            """
            
            from openai_handler import OpenAIHandler
            openai_handler = OpenAIHandler()
            image_description = await openai_handler.generate_text(description_prompt)
            
            return image_description if image_description else content[:200] + "..."
            
        except Exception as e:
            logger.error(f"Error creating image description: {str(e)}")
            return content[:200] + "..."

    def _create_pipeline_response(
        self, 
        pipeline_id: str, 
        stages: Dict[PipelineStage, StageResult], 
        start_time: float, 
        success: bool, 
        error: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create standardized pipeline response"""
        
        total_duration = time.time() - start_time
        
        # Convert stages to serializable format
        stages_data = {}
        for stage, result in stages.items():
            stages_data[stage.value] = {
                "status": result.status.value,
                "result": result.result,
                "error": result.error,
                "duration": round(result.duration, 2),
                "metadata": result.metadata
            }
        
        response = {
            "success": success,
            "pipeline_id": pipeline_id,
            "stages": stages_data,
            "total_duration": round(total_duration, 2),
            "timestamp": datetime.now().isoformat()
        }
        
        if error:
            response["error"] = error
        
        # Add final results if successful
        if success:
            final_content = stages.get(PipelineStage.CONTENT_GENERATION, StageResult(PipelineStage.CONTENT_GENERATION, StageStatus.SKIPPED)).result
            final_image = stages.get(PipelineStage.IMAGE_GENERATION, StageResult(PipelineStage.IMAGE_GENERATION, StageStatus.SKIPPED)).result
            final_post_id = stages.get(PipelineStage.LINKEDIN_POSTING, StageResult(PipelineStage.LINKEDIN_POSTING, StageStatus.SKIPPED)).result
            
            response["final_results"] = {
                "content": final_content,
                "image_path": final_image,
                "post_id": final_post_id
            }
        
        return response

    async def get_pipeline_status(self, pipeline_id: str) -> Dict[str, Any]:
        """Get status of a specific pipeline execution"""
        # This could be extended to store pipeline states in a database
        return {
            "pipeline_id": pipeline_id,
            "status": "completed",  # Placeholder
            "message": "Pipeline status tracking not implemented yet"
        } 