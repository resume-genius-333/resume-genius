"""Repository for job-related database operations."""

from typing import Optional, List
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.models.db.resumes.job import Job
from src.models.llm.resumes.job import JobLLMSchema


class JobRepository:
    """Repository for job database operations."""

    def __init__(self, session: AsyncSession):
        """Initialize job repository with database session."""
        self.session = session

    async def create_job(
        self,
        user_id: uuid.UUID,
        job_id: uuid.UUID,
        llm_schema: JobLLMSchema,
        job_url: Optional[str] = None,
    ) -> Job:
        """Create a new job in the database."""
        job = Job.from_llm(
            user_id=user_id,
            job_id=job_id,
            llm_schema=llm_schema,
            job_url=job_url,
        )

        self.session.add(job)
        await self.session.commit()
        await self.session.refresh(job)

        return job

    async def get_job_by_id(
        self, job_id: uuid.UUID, user_id: Optional[uuid.UUID] = None
    ) -> Optional[Job]:
        """Get a job by ID, optionally filtered by user."""
        query = select(Job).where(Job.id == job_id)

        if user_id:
            query = query.where(Job.user_id == user_id)

        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_job_with_relations(
        self, job_id: uuid.UUID, user_id: Optional[uuid.UUID] = None
    ) -> Optional[Job]:
        """Get a job with lazy loading for related entities."""
        query = select(Job).where(Job.id == job_id)

        if user_id:
            query = query.where(Job.user_id == user_id)

        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_jobs_by_user(
        self, user_id: uuid.UUID, limit: int = 50, offset: int = 0
    ) -> List[Job]:
        """Get all jobs for a specific user."""
        query = select(Job).where(Job.user_id == user_id).limit(limit).offset(offset)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def update_job(
        self, job_id: uuid.UUID, user_id: uuid.UUID, **kwargs
    ) -> Optional[Job]:
        """Update job fields."""
        job = await self.get_job_by_id(job_id, user_id)

        if not job:
            return None

        for key, value in kwargs.items():
            if hasattr(job, key):
                setattr(job, key, value)

        await self.session.commit()
        await self.session.refresh(job)

        return job

    async def delete_job(self, job_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        """Delete a job and all related entities."""
        job = await self.get_job_by_id(job_id, user_id)

        if not job:
            return False

        await self.session.delete(job)
        await self.session.commit()

        return True
