"""Repository for skill-related database operations."""

from typing import Optional, List
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from src.models.db.profile.skill import (
    ProfileSkill,
    ProfileSkillSchema,
    ProfileUserSkill,
    ProfileUserSkillSchema,
    ProfileTaskSkillMapping,
    ProfileTaskSkillMappingSchema,
    ProfileResponsibilitySkillMapping,
    ProfileResponsibilitySkillMappingSchema,
)
from src.models.llm.skill import SkillLLMSchema
from src.models.db.enums import SkillCategory, ProficiencyLevel


class SkillRepository:
    """Repository for skill database operations."""

    def __init__(self, session: AsyncSession):
        """Initialize skill repository with database session."""
        self.session = session

    # Skill methods
    async def create_skill(
        self,
        skill_id: uuid.UUID,
        llm_schema: SkillLLMSchema,
        embedding: List[float],
    ) -> ProfileSkillSchema:
        """Create a new skill record in the database."""
        skill = ProfileSkill.from_llm(
            skill_id=skill_id,
            llm_schema=llm_schema,
            embedding=embedding,
        )

        self.session.add(skill)
        await self.session.commit()
        await self.session.refresh(skill)

        return skill.schema

    async def get_skill_by_id(
        self, skill_id: uuid.UUID
    ) -> Optional[ProfileSkillSchema]:
        """Get a skill record by ID."""
        query = select(ProfileSkill).where(ProfileSkill.id == skill_id)
        result = await self.session.execute(query)
        skill = result.scalar_one_or_none()
        return skill.schema if skill else None

    async def get_skill_by_name(self, skill_name: str) -> Optional[ProfileSkillSchema]:
        """Get a skill record by name."""
        query = select(ProfileSkill).where(ProfileSkill.skill_name == skill_name)
        result = await self.session.execute(query)
        skill = result.scalar_one_or_none()
        return skill.schema if skill else None

    async def search_skills_by_embedding(
        self,
        embedding: List[float],
        limit: int = 10,
        similarity_threshold: Optional[float] = None,
    ) -> List[tuple[ProfileSkillSchema, float]]:
        """Search for similar skills using vector similarity."""
        # Using cosine similarity: <=> operator in pgvector
        query = (
            select(
                ProfileSkill,
                ProfileSkill.embedding.cosine_distance(embedding).label("distance"),
            )
            .order_by("distance")
            .limit(limit)
        )

        if similarity_threshold is not None:
            # Convert similarity threshold to distance (1 - similarity)
            distance_threshold = 1 - similarity_threshold
            query = query.filter(
                ProfileSkill.embedding.cosine_distance(embedding) <= distance_threshold
            )

        result = await self.session.execute(query)
        skills_with_distance = result.all()

        # Convert distance to similarity and return
        return [
            (skill.schema, 1 - distance)  # Convert distance back to similarity
            for skill, distance in skills_with_distance
        ]

    async def get_skills_by_category(
        self,
        category: SkillCategory,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[ProfileSkillSchema]:
        """Get all skills in a specific category."""
        query = select(ProfileSkill).where(ProfileSkill.skill_category == category)

        if limit:
            query = query.limit(limit)
        if offset:
            query = query.offset(offset)

        result = await self.session.execute(query)
        skills = list(result.scalars().all())
        return [skill.schema for skill in skills]

    async def update_skill(
        self, skill_id: uuid.UUID, **kwargs
    ) -> Optional[ProfileSkillSchema]:
        """Update skill fields."""
        query = select(ProfileSkill).where(ProfileSkill.id == skill_id)
        result = await self.session.execute(query)
        skill = result.scalar_one_or_none()

        if not skill:
            return None

        for key, value in kwargs.items():
            if hasattr(skill, key):
                setattr(skill, key, value)

        await self.session.commit()
        await self.session.refresh(skill)

        return skill.schema

    async def delete_skill(self, skill_id: uuid.UUID) -> bool:
        """Delete a skill record."""
        query = select(ProfileSkill).where(ProfileSkill.id == skill_id)
        result = await self.session.execute(query)
        skill = result.scalar_one_or_none()

        if not skill:
            return False

        await self.session.delete(skill)
        await self.session.commit()

        return True

    # UserSkill methods
    async def create_user_skill(
        self,
        user_id: uuid.UUID,
        skill_id: uuid.UUID,
        proficiency_level: Optional[ProficiencyLevel] = None,
    ) -> ProfileUserSkillSchema:
        """Create a user-skill association."""
        user_skill = ProfileUserSkill(
            user_id=user_id,
            skill_id=skill_id,
            proficiency_level=proficiency_level,
        )

        self.session.add(user_skill)
        await self.session.commit()
        await self.session.refresh(user_skill)

        return user_skill.schema

    async def get_user_skill(
        self,
        user_id: uuid.UUID,
        skill_id: uuid.UUID,
    ) -> Optional[ProfileUserSkillSchema]:
        """Get a specific user-skill association."""
        query = select(ProfileUserSkill).where(
            and_(
                ProfileUserSkill.user_id == user_id,
                ProfileUserSkill.skill_id == skill_id,
            )
        )
        result = await self.session.execute(query)
        user_skill = result.scalar_one_or_none()
        return user_skill.schema if user_skill else None

    async def get_user_skills(
        self,
        user_id: uuid.UUID,
        include_skill_details: bool = False,
    ) -> List[ProfileUserSkillSchema]:
        """Get all skills for a user."""
        query = select(ProfileUserSkill).where(ProfileUserSkill.user_id == user_id)

        if include_skill_details:
            query = query.options(selectinload(ProfileUserSkill.skill))

        result = await self.session.execute(query)
        user_skills = list(result.scalars().all())
        return [us.schema for us in user_skills]

    async def update_user_skill(
        self,
        user_id: uuid.UUID,
        skill_id: uuid.UUID,
        proficiency_level: ProficiencyLevel,
    ) -> Optional[ProfileUserSkillSchema]:
        """Update user skill proficiency level."""
        query = select(ProfileUserSkill).where(
            and_(
                ProfileUserSkill.user_id == user_id,
                ProfileUserSkill.skill_id == skill_id,
            )
        )
        result = await self.session.execute(query)
        user_skill = result.scalar_one_or_none()

        if not user_skill:
            return None

        user_skill.proficiency_level = proficiency_level
        await self.session.commit()
        await self.session.refresh(user_skill)

        return user_skill.schema

    async def delete_user_skill(self, user_id: uuid.UUID, skill_id: uuid.UUID) -> bool:
        """Delete a user-skill association."""
        query = select(ProfileUserSkill).where(
            and_(
                ProfileUserSkill.user_id == user_id,
                ProfileUserSkill.skill_id == skill_id,
            )
        )
        result = await self.session.execute(query)
        user_skill = result.scalar_one_or_none()

        if not user_skill:
            return False

        await self.session.delete(user_skill)
        await self.session.commit()

        return True

    # TaskSkillMapping methods
    async def create_task_skill_mapping(
        self,
        user_id: uuid.UUID,
        skill_id: uuid.UUID,
        task_id: uuid.UUID,
        justification: Optional[str] = None,
    ) -> ProfileTaskSkillMappingSchema:
        """Create a task-skill mapping."""
        mapping = ProfileTaskSkillMapping(
            user_id=user_id,
            skill_id=skill_id,
            task_id=task_id,
            justification=justification,
        )

        self.session.add(mapping)
        await self.session.commit()
        await self.session.refresh(mapping)

        return mapping.schema

    async def get_task_skill_mappings(
        self,
        task_id: uuid.UUID,
        user_id: Optional[uuid.UUID] = None,
    ) -> List[ProfileTaskSkillMappingSchema]:
        """Get all skill mappings for a task."""
        query = select(ProfileTaskSkillMapping).where(
            ProfileTaskSkillMapping.task_id == task_id
        )

        if user_id:
            query = query.where(ProfileTaskSkillMapping.user_id == user_id)

        result = await self.session.execute(query)
        mappings = list(result.scalars().all())
        return [mapping.schema for mapping in mappings]

    async def delete_task_skill_mapping(
        self,
        user_id: uuid.UUID,
        skill_id: uuid.UUID,
        task_id: uuid.UUID,
    ) -> bool:
        """Delete a task-skill mapping."""
        query = select(ProfileTaskSkillMapping).where(
            and_(
                ProfileTaskSkillMapping.user_id == user_id,
                ProfileTaskSkillMapping.skill_id == skill_id,
                ProfileTaskSkillMapping.task_id == task_id,
            )
        )
        result = await self.session.execute(query)
        mapping = result.scalar_one_or_none()

        if not mapping:
            return False

        await self.session.delete(mapping)
        await self.session.commit()

        return True

    # ResponsibilitySkillMapping methods
    async def create_responsibility_skill_mapping(
        self,
        user_id: uuid.UUID,
        skill_id: uuid.UUID,
        responsibility_id: uuid.UUID,
        justification: Optional[str] = None,
    ) -> ProfileResponsibilitySkillMappingSchema:
        """Create a responsibility-skill mapping."""
        mapping = ProfileResponsibilitySkillMapping(
            user_id=user_id,
            skill_id=skill_id,
            responsibility_id=responsibility_id,
            justification=justification,
        )

        self.session.add(mapping)
        await self.session.commit()
        await self.session.refresh(mapping)

        return mapping.schema

    async def get_responsibility_skill_mappings(
        self,
        responsibility_id: uuid.UUID,
        user_id: Optional[uuid.UUID] = None,
    ) -> List[ProfileResponsibilitySkillMappingSchema]:
        """Get all skill mappings for a responsibility."""
        query = select(ProfileResponsibilitySkillMapping).where(
            ProfileResponsibilitySkillMapping.responsibility_id == responsibility_id
        )

        if user_id:
            query = query.where(ProfileResponsibilitySkillMapping.user_id == user_id)

        result = await self.session.execute(query)
        mappings = list(result.scalars().all())
        return [mapping.schema for mapping in mappings]

    async def delete_responsibility_skill_mapping(
        self,
        user_id: uuid.UUID,
        skill_id: uuid.UUID,
        responsibility_id: uuid.UUID,
    ) -> bool:
        """Delete a responsibility-skill mapping."""
        query = select(ProfileResponsibilitySkillMapping).where(
            and_(
                ProfileResponsibilitySkillMapping.user_id == user_id,
                ProfileResponsibilitySkillMapping.skill_id == skill_id,
                ProfileResponsibilitySkillMapping.responsibility_id
                == responsibility_id,
            )
        )
        result = await self.session.execute(query)
        mapping = result.scalar_one_or_none()

        if not mapping:
            return False

        await self.session.delete(mapping)
        await self.session.commit()

        return True

    async def bulk_create_user_skills(
        self,
        user_id: uuid.UUID,
        skills_data: List[tuple[uuid.UUID, Optional[ProficiencyLevel]]],
    ) -> List[ProfileUserSkillSchema]:
        """Bulk create multiple user-skill associations."""
        user_skills = []
        for skill_id, proficiency_level in skills_data:
            user_skill = ProfileUserSkill(
                user_id=user_id,
                skill_id=skill_id,
                proficiency_level=proficiency_level,
            )
            user_skills.append(user_skill)
            self.session.add(user_skill)

        await self.session.commit()

        # Refresh all user skills
        for user_skill in user_skills:
            await self.session.refresh(user_skill)

        return [us.schema for us in user_skills]
