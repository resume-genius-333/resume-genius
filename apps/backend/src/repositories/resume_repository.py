"""Repository for resume-related database operations."""

from typing import Optional, List
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func

from src.models.db.resumes.resume import Resume
from src.models.db.resumes.resume_metadata import ResumeMetadata
from src.models.db.resumes.resume_education import ResumeEducation
from src.models.db.resumes.resume_work_experience import ResumeWorkExperience
from src.models.db.resumes.resume_project import ResumeProject
from src.models.db.resumes.resume_skill import ResumeSkill


class ResumeRepository:
    """Repository for resume version operations."""

    def __init__(self, session: AsyncSession):
        """Initialize resume repository with database session."""
        self.session = session

    async def create_version(
        self,
        user_id: uuid.UUID,
        job_id: uuid.UUID,
        metadata_id: uuid.UUID,
        parent_version: Optional[uuid.UUID] = None,
        pinned_education_ids: Optional[List[uuid.UUID]] = None,
        pinned_experience_ids: Optional[List[uuid.UUID]] = None,
        pinned_project_ids: Optional[List[uuid.UUID]] = None,
        pinned_skill_ids: Optional[List[uuid.UUID]] = None,
    ) -> Resume:
        """Create a new resume version."""
        resume = Resume(
            version=uuid.uuid4(),
            user_id=user_id,
            job_id=job_id,
            parent_version=parent_version,
            metadata_id=metadata_id,
            pinned_education_ids=pinned_education_ids or [],
            pinned_experience_ids=pinned_experience_ids or [],
            pinned_project_ids=pinned_project_ids or [],
            pinned_skill_ids=pinned_skill_ids or [],
        )

        self.session.add(resume)
        await self.session.flush()
        await self.session.refresh(resume)

        return resume

    async def get_version(
        self, version_id: uuid.UUID, user_id: Optional[uuid.UUID] = None
    ) -> Optional[Resume]:
        """Get a resume version by ID."""
        query = select(Resume).where(Resume.version == version_id)

        if user_id:
            query = query.where(Resume.user_id == user_id)

        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_latest_version(
        self, user_id: uuid.UUID, job_id: Optional[uuid.UUID] = None
    ) -> Optional[Resume]:
        """Get the latest resume version for a user."""
        query = select(Resume).where(Resume.user_id == user_id)

        if job_id:
            query = query.where(Resume.job_id == job_id)

        # query = query.order_by(Resume.created_at.desc()).limit(1)

        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def list_versions(
        self,
        user_id: uuid.UUID,
        job_id: Optional[uuid.UUID] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[List[Resume], int]:
        """List resume versions with pagination."""
        base_query = Resume.user_id == user_id

        if job_id:
            base_query = and_(base_query, Resume.job_id == job_id)

        # Get total count
        count_query = select(func.count()).where(base_query)
        total_result = await self.session.execute(count_query)
        total = total_result.scalar() or 0

        # Get paginated results
        query = (
            select(Resume)
            .where(base_query)
            # .order_by(Resume.created_at.desc())
            .limit(limit)
            .offset(offset)
        )

        result = await self.session.execute(query)
        versions = list(result.scalars().all())

        return versions, total

    async def update_version(
        self, version_id: uuid.UUID, user_id: uuid.UUID, **kwargs
    ) -> Optional[Resume]:
        """Update a resume version."""
        resume = await self.get_version(version_id, user_id)

        if not resume:
            return None

        for key, value in kwargs.items():
            if hasattr(resume, key):
                setattr(resume, key, value)

        await self.session.flush()
        await self.session.refresh(resume)

        return resume

    async def delete_version(self, version_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        """Delete a resume version."""
        resume = await self.get_version(version_id, user_id)

        if not resume:
            return False

        await self.session.delete(resume)
        await self.session.flush()

        return True


class ResumeMetadataRepository:
    """Repository for resume metadata operations."""

    def __init__(self, session: AsyncSession):
        """Initialize metadata repository with database session."""
        self.session = session

    async def create(
        self,
        user_id: uuid.UUID,
        job_id: uuid.UUID,
        user_name: str,
        parent_id: Optional[uuid.UUID] = None,
        **kwargs,
    ) -> ResumeMetadata:
        """Create new resume metadata."""
        metadata = ResumeMetadata(
            user_id=user_id,
            job_id=job_id,
            user_name=user_name,
            parent_id=parent_id,
            **kwargs,
        )

        self.session.add(metadata)
        await self.session.flush()
        await self.session.refresh(metadata)

        return metadata

    async def get_by_id(
        self, metadata_id: uuid.UUID, user_id: Optional[uuid.UUID] = None
    ) -> Optional[ResumeMetadata]:
        """Get metadata by ID."""
        query = select(ResumeMetadata).where(ResumeMetadata.id == metadata_id)

        if user_id:
            query = query.where(ResumeMetadata.user_id == user_id)

        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def update(
        self, metadata_id: uuid.UUID, user_id: uuid.UUID, **kwargs
    ) -> Optional[ResumeMetadata]:
        """Update resume metadata."""
        metadata = await self.get_by_id(metadata_id, user_id)

        if not metadata:
            return None

        for key, value in kwargs.items():
            if hasattr(metadata, key) and value is not None:
                setattr(metadata, key, value)

        await self.session.flush()
        await self.session.refresh(metadata)

        return metadata

    async def fork(
        self, metadata_id: uuid.UUID, user_id: uuid.UUID
    ) -> Optional[ResumeMetadata]:
        """Create a fork of existing metadata."""
        original = await self.get_by_id(metadata_id, user_id)

        if not original:
            return None

        new_metadata = ResumeMetadata(
            user_id=original.user_id,
            job_id=original.job_id,
            parent_id=original.id,
            user_name=original.user_name,
            email=original.email,
            phone=original.phone,
            location=original.location,
            linkedin_url=original.linkedin_url,
            github_url=original.github_url,
            portfolio_website=original.portfolio_website,
            custom_styles=original.custom_styles,
        )

        self.session.add(new_metadata)
        await self.session.flush()
        await self.session.refresh(new_metadata)

        return new_metadata


class ResumeEducationRepository:
    """Repository for resume education operations."""

    def __init__(self, session: AsyncSession):
        """Initialize education repository with database session."""
        self.session = session

    async def create(
        self,
        user_id: uuid.UUID,
        job_id: uuid.UUID,
        institution_name: str,
        degree: str,
        field_of_study: str,
        parent_id: Optional[uuid.UUID] = None,
        **kwargs,
    ) -> ResumeEducation:
        """Create new education entry."""
        education = ResumeEducation(
            user_id=user_id,
            job_id=job_id,
            institution_name=institution_name,
            degree=degree,
            field_of_study=field_of_study,
            parent_id=parent_id,
            **kwargs,
        )

        self.session.add(education)
        await self.session.flush()
        await self.session.refresh(education)

        return education

    async def get_by_id(
        self, education_id: uuid.UUID, user_id: Optional[uuid.UUID] = None
    ) -> Optional[ResumeEducation]:
        """Get education by ID."""
        query = select(ResumeEducation).where(ResumeEducation.id == education_id)

        if user_id:
            query = query.where(ResumeEducation.user_id == user_id)

        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_ids(
        self, education_ids: List[uuid.UUID], user_id: Optional[uuid.UUID] = None
    ) -> List[ResumeEducation]:
        """Get multiple education entries by IDs."""
        query = select(ResumeEducation).where(ResumeEducation.id.in_(education_ids))

        if user_id:
            query = query.where(ResumeEducation.user_id == user_id)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def list_by_user(
        self, user_id: uuid.UUID, job_id: Optional[uuid.UUID] = None
    ) -> List[ResumeEducation]:
        """List all education entries for a user."""
        query = select(ResumeEducation).where(ResumeEducation.user_id == user_id)

        if job_id:
            query = query.where(ResumeEducation.job_id == job_id)

        query = query.order_by(ResumeEducation.end_date.desc().nullslast())

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def update(
        self, education_id: uuid.UUID, user_id: uuid.UUID, **kwargs
    ) -> Optional[ResumeEducation]:
        """Update education entry."""
        education = await self.get_by_id(education_id, user_id)

        if not education:
            return None

        for key, value in kwargs.items():
            if hasattr(education, key) and value is not None:
                setattr(education, key, value)

        await self.session.flush()
        await self.session.refresh(education)

        return education

    async def fork(
        self, education_id: uuid.UUID, user_id: uuid.UUID
    ) -> Optional[ResumeEducation]:
        """Create a fork of existing education entry."""
        original = await self.get_by_id(education_id, user_id)

        if not original:
            return None

        new_education = ResumeEducation(
            user_id=original.user_id,
            job_id=original.job_id,
            parent_id=original.id,
            institution_name=original.institution_name,
            degree=original.degree,
            field_of_study=original.field_of_study,
            focus_area=original.focus_area,
            start_date=original.start_date,
            end_date=original.end_date,
            gpa=original.gpa,
            max_gpa=original.max_gpa,
            city=original.city,
            country=original.country,
        )

        self.session.add(new_education)
        await self.session.flush()
        await self.session.refresh(new_education)

        return new_education


class ResumeWorkExperienceRepository:
    """Repository for resume work experience operations."""

    def __init__(self, session: AsyncSession):
        """Initialize work experience repository with database session."""
        self.session = session

    async def create(
        self,
        user_id: uuid.UUID,
        job_id: uuid.UUID,
        job_title: str,
        company_name: str,
        parent_id: Optional[uuid.UUID] = None,
        **kwargs,
    ) -> ResumeWorkExperience:
        """Create new work experience entry."""
        work_exp = ResumeWorkExperience(
            user_id=user_id,
            job_id=job_id,
            job_title=job_title,
            company_name=company_name,
            parent_id=parent_id,
            **kwargs,
        )

        self.session.add(work_exp)
        await self.session.flush()
        await self.session.refresh(work_exp)

        return work_exp

    async def get_by_id(
        self, work_id: uuid.UUID, user_id: Optional[uuid.UUID] = None
    ) -> Optional[ResumeWorkExperience]:
        """Get work experience by ID."""
        query = select(ResumeWorkExperience).where(ResumeWorkExperience.id == work_id)

        if user_id:
            query = query.where(ResumeWorkExperience.user_id == user_id)

        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_ids(
        self, work_ids: List[uuid.UUID], user_id: Optional[uuid.UUID] = None
    ) -> List[ResumeWorkExperience]:
        """Get multiple work experience entries by IDs."""
        query = select(ResumeWorkExperience).where(
            ResumeWorkExperience.id.in_(work_ids)
        )

        if user_id:
            query = query.where(ResumeWorkExperience.user_id == user_id)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def list_by_user(
        self, user_id: uuid.UUID, job_id: Optional[uuid.UUID] = None
    ) -> List[ResumeWorkExperience]:
        """List all work experiences for a user."""
        query = select(ResumeWorkExperience).where(
            ResumeWorkExperience.user_id == user_id
        )

        if job_id:
            query = query.where(ResumeWorkExperience.job_id == job_id)

        query = query.order_by(ResumeWorkExperience.end_date.desc().nullslast())

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def update(
        self, work_id: uuid.UUID, user_id: uuid.UUID, **kwargs
    ) -> Optional[ResumeWorkExperience]:
        """Update work experience entry."""
        work_exp = await self.get_by_id(work_id, user_id)

        if not work_exp:
            return None

        for key, value in kwargs.items():
            if hasattr(work_exp, key) and value is not None:
                setattr(work_exp, key, value)

        await self.session.flush()
        await self.session.refresh(work_exp)

        return work_exp

    async def fork(
        self, work_id: uuid.UUID, user_id: uuid.UUID
    ) -> Optional[ResumeWorkExperience]:
        """Create a fork of existing work experience."""
        original = await self.get_by_id(work_id, user_id)

        if not original:
            return None

        new_work = ResumeWorkExperience(
            user_id=original.user_id,
            job_id=original.job_id,
            parent_id=original.id,
            job_title=original.job_title,
            company_name=original.company_name,
            employment_type=original.employment_type,
            start_date=original.start_date,
            end_date=original.end_date,
            location=original.location,
        )

        self.session.add(new_work)
        await self.session.flush()
        await self.session.refresh(new_work)

        return new_work


class ResumeProjectRepository:
    """Repository for resume project operations."""

    def __init__(self, session: AsyncSession):
        """Initialize project repository with database session."""
        self.session = session

    async def create(
        self,
        user_id: uuid.UUID,
        job_id: uuid.UUID,
        project_name: str,
        parent_id: Optional[uuid.UUID] = None,
        **kwargs,
    ) -> ResumeProject:
        """Create new project entry."""
        project = ResumeProject(
            user_id=user_id,
            job_id=job_id,
            project_name=project_name,
            parent_id=parent_id,
            **kwargs,
        )

        self.session.add(project)
        await self.session.flush()
        await self.session.refresh(project)

        return project

    async def get_by_id(
        self, project_id: uuid.UUID, user_id: Optional[uuid.UUID] = None
    ) -> Optional[ResumeProject]:
        """Get project by ID."""
        query = select(ResumeProject).where(ResumeProject.id == project_id)

        if user_id:
            query = query.where(ResumeProject.user_id == user_id)

        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_ids(
        self, project_ids: List[uuid.UUID], user_id: Optional[uuid.UUID] = None
    ) -> List[ResumeProject]:
        """Get multiple project entries by IDs."""
        query = select(ResumeProject).where(ResumeProject.id.in_(project_ids))

        if user_id:
            query = query.where(ResumeProject.user_id == user_id)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def list_by_user(
        self, user_id: uuid.UUID, job_id: Optional[uuid.UUID] = None
    ) -> List[ResumeProject]:
        """List all projects for a user."""
        query = select(ResumeProject).where(ResumeProject.user_id == user_id)

        if job_id:
            query = query.where(ResumeProject.job_id == job_id)

        query = query.order_by(ResumeProject.end_date.desc().nullslast())

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def update(
        self, project_id: uuid.UUID, user_id: uuid.UUID, **kwargs
    ) -> Optional[ResumeProject]:
        """Update project entry."""
        project = await self.get_by_id(project_id, user_id)

        if not project:
            return None

        for key, value in kwargs.items():
            if hasattr(project, key) and value is not None:
                setattr(project, key, value)

        await self.session.flush()
        await self.session.refresh(project)

        return project

    async def fork(
        self, project_id: uuid.UUID, user_id: uuid.UUID
    ) -> Optional[ResumeProject]:
        """Create a fork of existing project."""
        original = await self.get_by_id(project_id, user_id)

        if not original:
            return None

        new_project = ResumeProject(
            user_id=original.user_id,
            job_id=original.job_id,
            parent_id=original.id,
            project_name=original.project_name,
            role=original.role,
            start_date=original.start_date,
            end_date=original.end_date,
            location=original.location,
            description=original.description,
        )

        self.session.add(new_project)
        await self.session.flush()
        await self.session.refresh(new_project)

        return new_project


class ResumeSkillRepository:
    """Repository for resume skill operations."""

    def __init__(self, session: AsyncSession):
        """Initialize skill repository with database session."""
        self.session = session

    async def create(
        self,
        user_id: uuid.UUID,
        job_id: uuid.UUID,
        skill_name: str,
        parent_id: Optional[uuid.UUID] = None,
        **kwargs,
    ) -> ResumeSkill:
        """Create new skill entry."""
        skill = ResumeSkill(
            user_id=user_id,
            job_id=job_id,
            skill_name=skill_name,
            parent_id=parent_id,
            **kwargs,
        )

        self.session.add(skill)
        await self.session.flush()
        await self.session.refresh(skill)

        return skill

    async def get_by_id(
        self, skill_id: uuid.UUID, user_id: Optional[uuid.UUID] = None
    ) -> Optional[ResumeSkill]:
        """Get skill by ID."""
        query = select(ResumeSkill).where(ResumeSkill.id == skill_id)

        if user_id:
            query = query.where(ResumeSkill.user_id == user_id)

        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_ids(
        self, skill_ids: List[uuid.UUID], user_id: Optional[uuid.UUID] = None
    ) -> List[ResumeSkill]:
        """Get multiple skill entries by IDs."""
        query = select(ResumeSkill).where(ResumeSkill.id.in_(skill_ids))

        if user_id:
            query = query.where(ResumeSkill.user_id == user_id)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def list_by_user(
        self, user_id: uuid.UUID, job_id: Optional[uuid.UUID] = None
    ) -> List[ResumeSkill]:
        """List all skills for a user."""
        query = select(ResumeSkill).where(ResumeSkill.user_id == user_id)

        if job_id:
            query = query.where(ResumeSkill.job_id == job_id)

        query = query.order_by(ResumeSkill.skill_category, ResumeSkill.skill_name)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def update(
        self, skill_id: uuid.UUID, user_id: uuid.UUID, **kwargs
    ) -> Optional[ResumeSkill]:
        """Update skill entry."""
        skill = await self.get_by_id(skill_id, user_id)

        if not skill:
            return None

        for key, value in kwargs.items():
            if hasattr(skill, key) and value is not None:
                setattr(skill, key, value)

        await self.session.flush()
        await self.session.refresh(skill)

        return skill

    async def fork(
        self, skill_id: uuid.UUID, user_id: uuid.UUID
    ) -> Optional[ResumeSkill]:
        """Create a fork of existing skill."""
        original = await self.get_by_id(skill_id, user_id)

        if not original:
            return None

        new_skill = ResumeSkill(
            user_id=original.user_id,
            job_id=original.job_id,
            parent_id=original.id,
            skill_name=original.skill_name,
            skill_category=original.skill_category,
            proficiency_level=original.proficiency_level,
        )

        self.session.add(new_skill)
        await self.session.flush()
        await self.session.refresh(new_skill)

        return new_skill
