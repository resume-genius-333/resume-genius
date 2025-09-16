"""Repository for work experience-related database operations."""

from typing import Optional, List
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete
from src.models.db.work import (
    WorkExperience,
    WorkExperienceSchema,
    WorkResponsibility,
    WorkResponsibilitySchema,
)
from src.models.llm.work import WorkExperienceLLMSchema, WorkResponsibilityLLMSchema


class WorkRepository:
    """Repository for work experience database operations."""

    def __init__(self, session: AsyncSession):
        """Initialize work repository with database session."""
        self.session = session

    # WorkExperience methods
    async def create_work_experience(
        self,
        user_id: uuid.UUID,
        work_id: uuid.UUID,
        llm_schema: WorkExperienceLLMSchema,
    ) -> WorkExperienceSchema:
        """Create a new work experience record in the database."""
        work = WorkExperience.from_llm(
            user_id=user_id,
            work_id=work_id,
            llm_schema=llm_schema,
        )

        self.session.add(work)
        await self.session.commit()
        await self.session.refresh(work)

        return work.schema

    async def get_work_experience_by_id(
        self, work_id: uuid.UUID, user_id: Optional[uuid.UUID] = None
    ) -> Optional[WorkExperienceSchema]:
        """Get a work experience record by ID, optionally filtered by user."""
        query = select(WorkExperience).where(WorkExperience.id == work_id)

        if user_id:
            query = query.where(WorkExperience.user_id == user_id)

        result = await self.session.execute(query)
        work = result.scalar_one_or_none()
        return work.schema if work else None

    async def get_work_experiences_by_user(
        self,
        user_id: uuid.UUID,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[WorkExperienceSchema]:
        """Get all work experience records for a specific user."""
        query = select(WorkExperience).where(WorkExperience.user_id == user_id)

        # Order by end_date descending (most recent first), with NULL values first (current jobs)
        query = query.order_by(WorkExperience.end_date.desc().nullsfirst())

        if limit:
            query = query.limit(limit)
        if offset:
            query = query.offset(offset)

        result = await self.session.execute(query)
        works = list(result.scalars().all())
        return [work.schema for work in works]

    async def get_work_experiences_count(
        self,
        user_id: uuid.UUID,
    ) -> int:
        """Get the count of work experience records for a user."""
        query = select(func.count()).select_from(WorkExperience).where(WorkExperience.user_id == user_id)
        result = await self.session.scalar(query)
        return result or 0

    async def update_work_experience(
        self, work_id: uuid.UUID, user_id: uuid.UUID, **kwargs
    ) -> Optional[WorkExperienceSchema]:
        """Update work experience fields."""
        query = select(WorkExperience).where(WorkExperience.id == work_id).where(WorkExperience.user_id == user_id)
        result = await self.session.execute(query)
        work = result.scalar_one_or_none()

        if not work:
            return None

        for key, value in kwargs.items():
            if hasattr(work, key):
                setattr(work, key, value)

        await self.session.commit()
        await self.session.refresh(work)

        return work.schema

    async def delete_work_experience(self, work_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        """Delete a work experience record and all related responsibilities."""
        query = select(WorkExperience).where(WorkExperience.id == work_id).where(WorkExperience.user_id == user_id)
        result = await self.session.execute(query)
        work = result.scalar_one_or_none()

        if not work:
            return False

        await self.session.delete(work)
        await self.session.commit()

        return True

    # WorkResponsibility methods
    async def create_responsibility(
        self,
        user_id: uuid.UUID,
        work_id: uuid.UUID,
        responsibility_id: uuid.UUID,
        llm_schema: WorkResponsibilityLLMSchema,
    ) -> WorkResponsibilitySchema:
        """Create a new work responsibility record."""
        responsibility = WorkResponsibility.from_llm(
            user_id=user_id,
            work_id=work_id,
            responsibility_id=responsibility_id,
            llm_schema=llm_schema,
        )

        self.session.add(responsibility)
        await self.session.commit()
        await self.session.refresh(responsibility)

        return responsibility.schema

    async def get_responsibility_by_id(
        self, responsibility_id: uuid.UUID, user_id: Optional[uuid.UUID] = None
    ) -> Optional[WorkResponsibilitySchema]:
        """Get a work responsibility by ID."""
        query = select(WorkResponsibility).where(WorkResponsibility.id == responsibility_id)

        if user_id:
            query = query.where(WorkResponsibility.user_id == user_id)

        result = await self.session.execute(query)
        responsibility = result.scalar_one_or_none()
        return responsibility.schema if responsibility else None

    async def get_responsibilities_by_work(
        self,
        work_id: uuid.UUID,
        user_id: Optional[uuid.UUID] = None,
    ) -> List[WorkResponsibilitySchema]:
        """Get all responsibilities for a specific work experience."""
        query = select(WorkResponsibility).where(WorkResponsibility.work_id == work_id)

        if user_id:
            query = query.where(WorkResponsibility.user_id == user_id)

        result = await self.session.execute(query)
        responsibilities = list(result.scalars().all())
        return [resp.schema for resp in responsibilities]

    async def update_responsibility(
        self, responsibility_id: uuid.UUID, user_id: uuid.UUID, **kwargs
    ) -> Optional[WorkResponsibilitySchema]:
        """Update responsibility fields."""
        query = (
            select(WorkResponsibility)
            .where(WorkResponsibility.id == responsibility_id)
            .where(WorkResponsibility.user_id == user_id)
        )
        result = await self.session.execute(query)
        responsibility = result.scalar_one_or_none()

        if not responsibility:
            return None

        for key, value in kwargs.items():
            if hasattr(responsibility, key):
                setattr(responsibility, key, value)

        await self.session.commit()
        await self.session.refresh(responsibility)

        return responsibility.schema

    async def delete_responsibility(self, responsibility_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        """Delete a responsibility record."""
        query = (
            select(WorkResponsibility)
            .where(WorkResponsibility.id == responsibility_id)
            .where(WorkResponsibility.user_id == user_id)
        )
        result = await self.session.execute(query)
        responsibility = result.scalar_one_or_none()

        if not responsibility:
            return False

        await self.session.delete(responsibility)
        await self.session.commit()

        return True

    async def bulk_create_responsibilities(
        self,
        user_id: uuid.UUID,
        work_id: uuid.UUID,
        responsibilities_data: List[tuple[uuid.UUID, WorkResponsibilityLLMSchema]],
    ) -> List[WorkResponsibilitySchema]:
        """Bulk create multiple responsibility records for a work experience."""
        responsibilities = []
        for responsibility_id, llm_schema in responsibilities_data:
            responsibility = WorkResponsibility.from_llm(
                user_id=user_id,
                work_id=work_id,
                responsibility_id=responsibility_id,
                llm_schema=llm_schema,
            )
            responsibilities.append(responsibility)
            self.session.add(responsibility)

        await self.session.commit()

        # Refresh all responsibilities
        for responsibility in responsibilities:
            await self.session.refresh(responsibility)

        return [resp.schema for resp in responsibilities]

    async def delete_responsibilities_by_work(self, work_id: uuid.UUID, user_id: uuid.UUID) -> int:
        """Delete all responsibilities for a specific work experience."""
        stmt = delete(WorkResponsibility).where(
            WorkResponsibility.work_id == work_id,
            WorkResponsibility.user_id == user_id
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount