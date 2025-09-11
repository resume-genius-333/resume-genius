"""Service for job-related business logic."""

from typing import Optional
import uuid
import logging
from instructor import AsyncInstructor

from src.repositories.job_repository import JobRepository
from src.services.status_service import StatusService
from src.models.db.resumes.job import Job, JobSchema
from src.models.llm.resumes.job import JobLLMSchema

logger = logging.getLogger(__name__)


class JobService:
    """Service for job business logic."""

    def __init__(
        self,
        repository: JobRepository,
        status_service: StatusService,
        instructor: AsyncInstructor,
    ):
        """Initialize job service with dependencies."""
        self.repository = repository
        self.status_service = status_service
        self.instructor = instructor

    async def create_job(
        self,
        user_id: uuid.UUID,
        job_id: uuid.UUID,
        job_description: str,
        job_url: Optional[str] = None,
    ) -> Job:
        """Create a new job by extracting information using LLM."""
        logger.info(f"Starting job creation for user_id={user_id}, job_id={job_id}")
        
        try:
            # Extract job information using LLM
            logger.info("Calling LLM with job description")
            llm_result = await self.instructor.create(
                model="gpt-5-nano",
                response_model=JobLLMSchema,
                messages=[
                    {
                        "role": "user",
                        "content": f"Extract information from the job description. \n\n{job_description}",
                    }
                ],
            )
            logger.info(f"LLM response received: {llm_result.model_dump_json(indent=2)}")

            # Create job in database
            logger.info("Creating job in database")
            job = await self.repository.create_job(
                user_id=user_id,
                job_id=job_id,
                llm_schema=llm_result,
                job_url=job_url,
            )
            logger.info(f"Job saved to database: job_id={job_id}")

            # Update processing status
            await self.status_service.set_and_publish_status(
                user_id=user_id,
                job_id=job_id,
                tag="job-parsed-at",
            )

            return job

        except Exception as e:
            logger.error(f"Error in create_job: {str(e)}")
            await self.repository.rollback()
            raise

    async def get_job(
        self, 
        job_id: uuid.UUID,
        user_id: Optional[uuid.UUID] = None
    ) -> Optional[JobSchema]:
        """Get a job by ID."""
        job = await self.repository.get_job_by_id(job_id, user_id)
        
        if job:
            return job.schema
        
        return None

    async def get_user_jobs(
        self,
        user_id: uuid.UUID,
        limit: int = 50,
        offset: int = 0
    ) -> list[JobSchema]:
        """Get all jobs for a user."""
        jobs = await self.repository.get_jobs_by_user(user_id, limit, offset)
        return [job.schema for job in jobs]

    async def select_relevant_info(
        self,
        job_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> dict:
        """Select relevant information from user's resume for the job."""
        # TODO: Implement resume information selection logic
        # This will involve:
        # 1. Getting the job details
        # 2. Getting user's resume information
        # 3. Using LLM to select relevant experiences/skills
        # 4. Storing the selected information
        
        logger.info(f"Selecting relevant info for job_id={job_id}, user_id={user_id}")
        
        # Placeholder implementation
        return {
            "status": "pending",
            "message": "Feature not yet implemented"
        }

    async def refine_resume(
        self,
        job_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> dict:
        """Refine user's resume for the specific job."""
        # TODO: Implement resume refinement logic
        # This will involve:
        # 1. Getting the selected relevant information
        # 2. Using LLM to refine and optimize resume content
        # 3. Generating the refined resume
        # 4. Storing the refined version
        
        logger.info(f"Refining resume for job_id={job_id}, user_id={user_id}")
        
        # Placeholder implementation
        return {
            "status": "success",
            "message": "Resume refinement started"
        }

    async def delete_job(
        self,
        job_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> bool:
        """Delete a job and all related data."""
        return await self.repository.delete_job(job_id, user_id)