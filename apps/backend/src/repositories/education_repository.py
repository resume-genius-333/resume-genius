"""Repository for education-related database operations."""

from typing import Optional, List
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from src.models.db.profile.education import (
    ProfileEducation,
    ProfileEducationSchema,
)
from src.models.llm.education import EducationLLMSchema


class EducationRepository:
    """Repository for education database operations."""

    def __init__(self, session: AsyncSession):
        """Initialize education repository with database session."""
        self.session = session

    async def create_education(
        self,
        user_id: uuid.UUID,
        education_id: uuid.UUID,
        llm_schema: EducationLLMSchema,
    ) -> ProfileEducationSchema:
        """Create a new education record in the database."""
        education = ProfileEducation.from_llm(
            user_id=user_id,
            education_id=education_id,
            llm_schema=llm_schema,
        )

        self.session.add(education)
        await self.session.commit()
        await self.session.refresh(education)

        return education.schema

    async def get_education_by_id(
        self, education_id: uuid.UUID, user_id: Optional[uuid.UUID] = None
    ) -> Optional[ProfileEducationSchema]:
        """Get an education record by ID, optionally filtered by user."""
        query = select(ProfileEducation).where(ProfileEducation.id == education_id)

        if user_id:
            query = query.where(ProfileEducation.user_id == user_id)

        result = await self.session.execute(query)
        education = result.scalar_one_or_none()
        return education.schema if education else None

    async def get_educations_by_user(
        self,
        user_id: uuid.UUID,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[ProfileEducationSchema]:
        """Get all education records for a specific user."""
        query = select(ProfileEducation).where(ProfileEducation.user_id == user_id)

        # Order by end_date descending (most recent first), with NULL values last
        query = query.order_by(ProfileEducation.end_date.desc().nullslast())

        if limit:
            query = query.limit(limit)
        if offset:
            query = query.offset(offset)

        result = await self.session.execute(query)
        educations = list(result.scalars().all())
        return [education.schema for education in educations]

    async def get_educations_count(
        self,
        user_id: uuid.UUID,
    ) -> int:
        """Get the count of education records for a user."""
        query = (
            select(func.count())
            .select_from(ProfileEducation)
            .where(ProfileEducation.user_id == user_id)
        )
        result = await self.session.scalar(query)
        return result or 0

    async def update_education(
        self, education_id: uuid.UUID, user_id: uuid.UUID, **kwargs
    ) -> Optional[ProfileEducationSchema]:
        """Update education fields."""
        query = (
            select(ProfileEducation)
            .where(ProfileEducation.id == education_id)
            .where(ProfileEducation.user_id == user_id)
        )
        result = await self.session.execute(query)
        education = result.scalar_one_or_none()

        if not education:
            return None

        for key, value in kwargs.items():
            if hasattr(education, key):
                setattr(education, key, value)

        await self.session.commit()
        await self.session.refresh(education)

        return education.schema

    async def delete_education(
        self, education_id: uuid.UUID, user_id: uuid.UUID
    ) -> bool:
        """Delete an education record."""
        query = (
            select(ProfileEducation)
            .where(ProfileEducation.id == education_id)
            .where(ProfileEducation.user_id == user_id)
        )
        result = await self.session.execute(query)
        education = result.scalar_one_or_none()

        if not education:
            return False

        await self.session.delete(education)
        await self.session.commit()

        return True

    async def bulk_create_educations(
        self,
        user_id: uuid.UUID,
        educations_data: List[tuple[uuid.UUID, EducationLLMSchema]],
    ) -> List[ProfileEducationSchema]:
        """Bulk create multiple education records."""
        educations = []
        for education_id, llm_schema in educations_data:
            education = ProfileEducation.from_llm(
                user_id=user_id,
                education_id=education_id,
                llm_schema=llm_schema,
            )
            educations.append(education)
            self.session.add(education)

        await self.session.commit()

        # Refresh all educations
        for education in educations:
            await self.session.refresh(education)

        return [education.schema for education in educations]
