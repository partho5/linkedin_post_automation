import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Callable
import json
import os
from dataclasses import dataclass, asdict
from enum import Enum
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)
logger = logging.getLogger("linkedin_api_post")


class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ScheduledTask:
    task_id: str
    task_type: str
    scheduled_time: datetime
    payload: Dict[str, Any]
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


class ContentScheduler:
    def __init__(self):
        try:
            self.tasks: Dict[str, ScheduledTask] = {}
            self.running_tasks: Dict[str, asyncio.Task] = {}
            self.max_retries = int(os.getenv('MAX_RETRIES', '3'))
            self.retry_delay = int(os.getenv('RETRY_DELAY', '5'))
            self.scheduler_running = False
            self.scheduler_task = None

            # Task callbacks - will be set by main application
            self.task_callbacks: Dict[str, Callable] = {}

            logger.info("Content Scheduler initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize Content Scheduler: {str(e)}")
            raise

    async def start_scheduler(self) -> Dict[str, Any]:
        """Start the background scheduler"""
        try:
            if self.scheduler_running:
                return {"status": "already_running", "message": "Scheduler is already active"}

            self.scheduler_running = True
            self.scheduler_task = asyncio.create_task(self._scheduler_loop())

            logger.info("Content scheduler started successfully")
            return {"status": "started", "message": "Scheduler started successfully"}

        except Exception as e:
            logger.error(f"Failed to start scheduler: {str(e)}")
            return {"status": "error", "error": str(e)}

    async def stop_scheduler(self) -> Dict[str, Any]:
        """Stop the background scheduler"""
        try:
            if not self.scheduler_running:
                return {"status": "already_stopped", "message": "Scheduler is not running"}

            self.scheduler_running = False

            if self.scheduler_task:
                self.scheduler_task.cancel()
                try:
                    await self.scheduler_task
                except asyncio.CancelledError:
                    pass

            # Cancel all running tasks
            for task_id, task in self.running_tasks.items():
                task.cancel()
                logger.info(f"Cancelled running task: {task_id}")

            self.running_tasks.clear()

            logger.info("Content scheduler stopped successfully")
            return {"status": "stopped", "message": "Scheduler stopped successfully"}

        except Exception as e:
            logger.error(f"Failed to stop scheduler: {str(e)}")
            return {"status": "error", "error": str(e)}

    async def schedule_post_creation(self, task_id: str, scheduled_time: datetime, payload: Dict[str, Any]) -> Dict[
        str, Any]:
        """Schedule a new post creation task"""
        try:
            if task_id in self.tasks:
                return {
                    "success": False,
                    "error": f"Task with ID {task_id} already exists",
                    "task_id": task_id
                }

            # Validate scheduled time
            if scheduled_time <= datetime.now():
                return {
                    "success": False,
                    "error": "Scheduled time must be in the future",
                    "scheduled_time": scheduled_time.isoformat()
                }

            # Create scheduled task
            task = ScheduledTask(
                task_id=task_id,
                task_type="post_creation",
                scheduled_time=scheduled_time,
                payload=payload,
                max_retries=self.max_retries
            )

            self.tasks[task_id] = task

            logger.info(f"Post creation scheduled: {task_id} at {scheduled_time}")

            return {
                "success": True,
                "task_id": task_id,
                "scheduled_time": scheduled_time.isoformat(),
                "status": "scheduled"
            }

        except Exception as e:
            logger.error(f"Failed to schedule post creation: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "task_id": task_id
            }

    async def cancel_scheduled_task(self, task_id: str) -> Dict[str, Any]:
        """Cancel a scheduled task"""
        try:
            if task_id not in self.tasks:
                return {
                    "success": False,
                    "error": f"Task {task_id} not found",
                    "task_id": task_id
                }

            task = self.tasks[task_id]

            # Cancel running task if exists
            if task_id in self.running_tasks:
                self.running_tasks[task_id].cancel()
                del self.running_tasks[task_id]

            # Update task status
            task.status = TaskStatus.CANCELLED
            task.completed_at = datetime.now()

            logger.info(f"Task cancelled: {task_id}")

            return {
                "success": True,
                "task_id": task_id,
                "status": "cancelled",
                "cancelled_at": task.completed_at.isoformat()
            }

        except Exception as e:
            logger.error(f"Failed to cancel task {task_id}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "task_id": task_id
            }

    async def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Get status of a specific task"""
        try:
            if task_id not in self.tasks:
                return {
                    "found": False,
                    "error": f"Task {task_id} not found",
                    "task_id": task_id
                }

            task = self.tasks[task_id]

            return {
                "found": True,
                "task_id": task.task_id,
                "status": task.status.value,
                "task_type": task.task_type,
                "scheduled_time": task.scheduled_time.isoformat(),
                "created_at": task.created_at.isoformat(),
                "started_at": task.started_at.isoformat() if task.started_at else None,
                "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                "retry_count": task.retry_count,
                "max_retries": task.max_retries,
                "error_message": task.error_message,
                "is_running": task_id in self.running_tasks
            }

        except Exception as e:
            logger.error(f"Failed to get task status for {task_id}: {str(e)}")
            return {
                "found": False,
                "error": str(e),
                "task_id": task_id
            }

    async def list_all_tasks(self, status_filter: Optional[str] = None) -> Dict[str, Any]:
        """List all tasks with optional status filtering"""
        try:
            tasks_list = []

            for task in self.tasks.values():
                if status_filter and task.status.value != status_filter:
                    continue

                task_info = {
                    "task_id": task.task_id,
                    "status": task.status.value,
                    "task_type": task.task_type,
                    "scheduled_time": task.scheduled_time.isoformat(),
                    "created_at": task.created_at.isoformat(),
                    "retry_count": task.retry_count,
                    "is_running": task.task_id in self.running_tasks
                }

                if task.error_message:
                    task_info["error_message"] = task.error_message

                tasks_list.append(task_info)

            # Sort by scheduled time
            tasks_list.sort(key=lambda x: x["scheduled_time"])

            return {
                "total_tasks": len(tasks_list),
                "filter": status_filter,
                "tasks": tasks_list,
                "scheduler_running": self.scheduler_running
            }

        except Exception as e:
            logger.error(f"Failed to list tasks: {str(e)}")
            return {
                "error": str(e),
                "total_tasks": 0,
                "tasks": []
            }

    async def monitor_pipeline_status(self, task_id: str) -> Dict[str, Any]:
        """Monitor the complete pipeline status for a task"""
        try:
            task_status = await self.get_task_status(task_id)

            if not task_status.get("found"):
                return task_status

            # Add pipeline-specific monitoring
            pipeline_info = {
                "pipeline_stages": [
                    "content_generation",
                    "image_generation",
                    "linkedin_posting"
                ],
                "current_stage": self._get_current_pipeline_stage(task_id),
                "stages_completed": self._get_completed_stages(task_id),
                "estimated_completion": self._estimate_completion_time(task_id)
            }

            # Merge task status with pipeline info
            result = {**task_status, **pipeline_info}

            return result

        except Exception as e:
            logger.error(f"Failed to monitor pipeline status for {task_id}: {str(e)}")
            return {
                "error": str(e),
                "task_id": task_id,
                "pipeline_status": "error"
            }

    def register_task_callback(self, task_type: str, callback: Callable) -> None:
        """Register a callback function for a specific task type"""
        self.task_callbacks[task_type] = callback
        logger.info(f"Registered callback for task type: {task_type}")

    async def _scheduler_loop(self) -> None:
        """Main scheduler loop that runs in the background"""
        try:
            while self.scheduler_running:
                try:
                    await self._process_due_tasks()
                    await asyncio.sleep(30)  # Check every 30 seconds
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"Error in scheduler loop: {str(e)}")
                    await asyncio.sleep(60)  # Wait longer on error

        except asyncio.CancelledError:
            logger.info("Scheduler loop cancelled")
        except Exception as e:
            logger.error(f"Scheduler loop failed: {str(e)}")

    async def _process_due_tasks(self) -> None:
        """Process tasks that are due for execution"""
        try:
            current_time = datetime.now()

            for task_id, task in self.tasks.items():
                if (task.status == TaskStatus.PENDING and
                        task.scheduled_time <= current_time and
                        task_id not in self.running_tasks):
                    # Start the task
                    task_coroutine = self._execute_task(task_id)
                    self.running_tasks[task_id] = asyncio.create_task(task_coroutine)

                    logger.info(f"Started execution of task: {task_id}")

        except Exception as e:
            logger.error(f"Error processing due tasks: {str(e)}")

    async def _execute_task(self, task_id: str) -> None:
        """Execute a specific task"""
        try:
            task = self.tasks[task_id]
            task.status = TaskStatus.RUNNING
            task.started_at = datetime.now()

            # Get the appropriate callback for this task type
            callback = self.task_callbacks.get(task.task_type)

            if not callback:
                raise Exception(f"No callback registered for task type: {task.task_type}")

            # Execute the task
            result = await callback(task.payload)

            if result.get("success", False):
                task.status = TaskStatus.COMPLETED
                task.completed_at = datetime.now()
                logger.info(f"Task completed successfully: {task_id}")
            else:
                raise Exception(result.get("error", "Task execution failed"))

        except Exception as e:
            task = self.tasks[task_id]
            task.retry_count += 1
            task.error_message = str(e)

            if task.retry_count < task.max_retries:
                # Schedule retry
                task.status = TaskStatus.PENDING
                task.scheduled_time = datetime.now() + timedelta(minutes=self.retry_delay)
                logger.warning(f"Task {task_id} failed, scheduling retry {task.retry_count}/{task.max_retries}")
            else:
                task.status = TaskStatus.FAILED
                task.completed_at = datetime.now()
                logger.error(f"Task {task_id} failed permanently after {task.retry_count} retries: {str(e)}")

        finally:
            # Clean up running task reference
            if task_id in self.running_tasks:
                del self.running_tasks[task_id]

    def _get_current_pipeline_stage(self, task_id: str) -> str:
        """Get current pipeline stage for a task"""
        # This would be implemented based on task payload and progress
        return "content_generation"  # Placeholder

    def _get_completed_stages(self, task_id: str) -> List[str]:
        """Get list of completed pipeline stages"""
        # This would be implemented based on task progress tracking
        return []  # Placeholder

    def _estimate_completion_time(self, task_id: str) -> Optional[str]:
        """Estimate completion time for a task"""
        try:
            task = self.tasks.get(task_id)
            if not task or task.status not in [TaskStatus.RUNNING, TaskStatus.PENDING]:
                return None

            # Rough estimation based on typical pipeline duration
            estimated_minutes = 5  # Placeholder estimation
            estimated_time = datetime.now() + timedelta(minutes=estimated_minutes)

            return estimated_time.isoformat()

        except Exception as e:
            logger.error(f"Error estimating completion time: {str(e)}")
            return None

from fastapi import FastAPI, Depends, HTTPException, status, Request, Body
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from uuid import uuid4
from datetime import datetime
import traceback

from ai_writer import AIWriter
from image_generation_handler import ImageHandler
from linkedin_api_handler import LinkedInAPI
from linkedin_oauth_handler import LinkedInOAuthHandler

# Configure logging
logging.basicConfig(level=logging.INFO)

async def main():
    # Get LinkedIn OAuth configuration from environment variables
    client_id = os.getenv('LINKEDIN_CLIENT_ID')
    client_secret = os.getenv('LINKEDIN_CLIENT_SECRET')
    redirect_uri = os.getenv('LINKEDIN_CALLBACK_URL')
    
    if not all([client_id, client_secret, redirect_uri]):
        print("Missing required LinkedIn OAuth environment variables:")
        print("- LINKEDIN_CLIENT_ID")
        print("- LINKEDIN_CLIENT_SECRET") 
        print("- LINKEDIN_CALLBACK_URL")
        return
    
    # Initialize OAuth handler
    oauth_handler = LinkedInOAuthHandler(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri
    )
    
    # Get authorization code from environment variable
    authorization_code = os.getenv('LINKEDIN_AUTH_CODE')
    if not authorization_code:
        print("LINKEDIN_AUTH_CODE environment variable not set. Please set it with the authorization code from the LinkedIn redirect URL.")
        return
    
    try:
        # Exchange code for tokens
        token_data = await oauth_handler.exchange_code_for_token(authorization_code)
        print(f"Token exchange successful: {token_data.get('access_token', 'No token')[:20]}...")
        
        # Initialize LinkedIn API with OAuth handler
        linkedin_api = LinkedInAPI(oauth_handler=oauth_handler)
        
        # Validate credentials
        validation_result = await linkedin_api.validate_credentials()
        if validation_result.get("valid"):
            print("LinkedIn credentials validated successfully")
            
            # Post text-only content
            text_result = await linkedin_api.post_content("This is a test post from the LinkedIn API integration!")
            print(f"Text post result: {text_result}")
            
            # Post with image (if image exists)
            image_path = "assets/media/image/photo.png"
            image_result = await linkedin_api.post_content(
                "This is a test post with an image!",
                image_path=image_path
            )
            print(f"Image post result: {image_result}")
            
        else:
            print(f"Credential validation failed: {validation_result}")
            
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())

app = FastAPI(title="LinkedIn Content Automation API")

# Security
security = HTTPBearer()
BASIC_AUTH_TOKEN = os.getenv("BASIC_AUTH_TOKEN")

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if not BASIC_AUTH_TOKEN or credentials.credentials != BASIC_AUTH_TOKEN:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or missing token")

# Models
class GenerateContentRequest(BaseModel):
    topic: str
    style_params: str = None

class GenerateImageRequest(BaseModel):
    content_description: str
    style: str = None

class PostToLinkedInRequest(BaseModel):
    content: str
    image: str = None  # path to image file

class SchedulePostRequest(BaseModel):
    datetime: str  # ISO format
    content: str
    image: str = None

class LinkedInOAuthRequest(BaseModel):
    auth_code: str

class LinkedInPostRequest(BaseModel):
    content: str
    image_path: str = "assets/media/image/photo.png"

# Handlers
ai_writer = AIWriter()
image_handler = ImageHandler()
linkedin_api = LinkedInAPI()
scheduler = ContentScheduler()

# Register scheduler callbacks
def scheduler_post_callback(payload):
    async def _cb(payload):
        # Generate content
        content = payload.get("content")
        image = payload.get("image")
        if not content:
            topic = payload.get("topic")
            style = payload.get("style")
            content = await ai_writer.generate_post_content(topic, style)
        # Generate image if not provided
        if not image:
            image = await image_handler.generate_post_image(content)
        # Post to LinkedIn
        result = await linkedin_api.post_content(content, image)
        return result
    return _cb(payload)

scheduler.register_task_callback("post_creation", scheduler_post_callback)

@app.on_event("startup")
async def startup_event():
    await scheduler.start_scheduler()

@app.on_event("shutdown")
async def shutdown_event():
    await scheduler.stop_scheduler()

@app.get("/api/v1/health-check")
def health_check():
    return {"status": "ok"}

@app.post("/api/v1/generate-content", dependencies=[Depends(verify_token)])
async def generate_content(req: GenerateContentRequest):
    try:
        content = await ai_writer.generate_post_content(req.topic, req.style_params)
        if not content:
            raise HTTPException(status_code=500, detail="Content generation failed")
        return {"success": True, "content": content}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/generate-image", dependencies=[Depends(verify_token)])
async def generate_image(req: GenerateImageRequest):
    try:
        image_path = await image_handler.generate_post_image(req.content_description, req.style)
        if not image_path:
            raise HTTPException(status_code=500, detail="Image generation failed")
        return {"success": True, "image_path": image_path}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/post-linkedin", dependencies=[Depends(verify_token)])
async def post_linkedin(req: PostToLinkedInRequest = Body(...)):
    try:
        logger.info(f"Received post-linkedin request: content length={len(req.content) if req.content else 0}, image={req.image}")
        # Ensure image is optional and handled gracefully
        image = req.image if req.image else None
        result = await linkedin_api.post_content(req.content, image)
        logger.info(f"LinkedIn API post_content result: {result}")
        if not result.get("success"):
            logger.error(f"LinkedIn post failed: {result}")
            raise HTTPException(status_code=500, detail=result.get("error", "LinkedIn post failed"))
        return result
    except Exception as e:
        logger.error(f"Exception in post_linkedin: {str(e)}\nRequest: {req.dict() if hasattr(req, 'dict') else req}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/schedule-post", dependencies=[Depends(verify_token)])
async def schedule_post(req: SchedulePostRequest):
    try:
        # Validate datetime
        try:
            scheduled_time = datetime.fromisoformat(req.datetime)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid datetime format. Use ISO format.")
        task_id = str(uuid4())
        payload = {"content": req.content, "image": req.image}
        result = await scheduler.schedule_post_creation(task_id, scheduled_time, payload)
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "Scheduling failed"))
        return {"success": True, "task_id": task_id, "scheduled_time": scheduled_time.isoformat()}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/status/{job_id}", dependencies=[Depends(verify_token)])
async def pipeline_status(job_id: str):
    try:
        status = await scheduler.monitor_pipeline_status(job_id)
        if not status.get("found", True):
            raise HTTPException(status_code=404, detail=status.get("error", "Job not found"))
        return status
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/linkedin/exchange-token", dependencies=[Depends(verify_token)])
async def exchange_linkedin_token(req: LinkedInOAuthRequest):
    """Exchange LinkedIn authorization code for access token"""
    try:
        # Get LinkedIn OAuth configuration from environment variables
        client_id = os.getenv('LINKEDIN_CLIENT_ID')
        client_secret = os.getenv('LINKEDIN_CLIENT_SECRET')
        redirect_uri = os.getenv('LINKEDIN_CALLBACK_URL')
        
        if not all([client_id, client_secret, redirect_uri]):
            return {
                "success": False,
                "error": "Missing required LinkedIn OAuth environment variables"
            }
        
        # Initialize OAuth handler
        oauth_handler = LinkedInOAuthHandler(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri
        )
        
        # Exchange code for tokens
        token_data = await oauth_handler.exchange_code_for_token(req.auth_code)

        print(f"access_token={token_data.get('access_token', '')}")
        
        return {
            "success": True,
            "message": "Token exchange successful",
            "token_info": {
                "access_token": token_data.get('access_token', '')[:20] + "...",
                "expires_in": token_data.get('expires_in'),
                "token_type": token_data.get('token_type')
            }
        }
        
    except Exception as e:
        logger.error(f"LinkedIn token exchange error: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

@app.post("/api/v1/linkedin/post", dependencies=[Depends(verify_token)])
async def post_to_linkedin(req: LinkedInPostRequest):
    """Post content to LinkedIn using OAuth tokens"""
    try:
        # Get LinkedIn OAuth configuration from environment variables
        client_id = os.getenv('LINKEDIN_CLIENT_ID')
        client_secret = os.getenv('LINKEDIN_CLIENT_SECRET')
        redirect_uri = os.getenv('LINKEDIN_CALLBACK_URL')
        
        if not all([client_id, client_secret, redirect_uri]):
            return {
                "success": False,
                "error": "Missing required LinkedIn OAuth environment variables"
            }
        
        # Initialize OAuth handler
        oauth_handler = LinkedInOAuthHandler(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri
        )
        
        # Initialize LinkedIn API with OAuth handler
        linkedin_api = LinkedInAPI(oauth_handler=oauth_handler)
        
        # Post content using the new 6-step flow (no validation needed)
        result = await linkedin_api.post_content(req.content, req.image_path)
        
        return {
            "success": result.get("success", False),
            "result": result
        }
        
    except Exception as e:
        logger.error(f"LinkedIn posting error: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }