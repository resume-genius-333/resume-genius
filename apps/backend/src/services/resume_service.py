"""Service for resume-related business logic."""

from typing import Optional, List
import uuid
import logging
from dependency_injector.wiring import Provide, inject
from instructor import AsyncInstructor

from src.containers import Container, container
from src.core.unit_of_work import UnitOfWork
from src.models.api.resume import (
    FullResumeResponse,
    AIEnhanceRequest,
)
from src.models.db.resumes.resume import ResumeSchema
from src.models.db.resumes.resume_education import ResumeEducationSchema
from src.models.db.resumes.resume_metadata import ResumeMetadataSchema
from src.models.db.resumes.resume_project import ResumeProjectSchema
from src.models.db.resumes.resume_skill import ResumeSkillSchema
from src.models.db.resumes.resume_work_experience import ResumeWorkExperienceSchema

logger = logging.getLogger(__name__)
container.wire(modules=[__name__])


class ResumeService:
    """Service for resume business logic."""

    @inject
    def __init__(
        self,
        uow: UnitOfWork,
        instructor: AsyncInstructor = Provide[Container.async_instructor],
    ):
        """Initialize resume service with dependencies."""
        self.uow = uow
        self.instructor = instructor

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
    ) -> ResumeSchema:
        """Create a new resume version."""
        resume = await self.uow.resume_repository.create_version(
            user_id=user_id,
            job_id=job_id,
            metadata_id=metadata_id,
            parent_version=parent_version,
            pinned_education_ids=pinned_education_ids,
            pinned_experience_ids=pinned_experience_ids,
            pinned_project_ids=pinned_project_ids,
            pinned_skill_ids=pinned_skill_ids,
        )
        return resume.schema

    async def get_version(
        self, version_id: uuid.UUID, user_id: Optional[uuid.UUID] = None
    ) -> Optional[ResumeSchema]:
        """Get a resume version by ID."""
        resume = await self.uow.resume_repository.get_version(version_id, user_id)

        if not resume:
            return None

        return resume.schema

    async def get_latest_version(
        self, user_id: uuid.UUID, job_id: Optional[uuid.UUID] = None
    ) -> Optional[ResumeSchema]:
        """Get the latest resume version for a user."""
        resume = await self.uow.resume_repository.get_latest_version(user_id, job_id)

        if not resume:
            return None

        return resume.schema

    async def list_versions(
        self,
        user_id: uuid.UUID,
        job_id: Optional[uuid.UUID] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[List[ResumeSchema], int]:
        """List resume versions with pagination."""
        resumes, total = await self.uow.resume_repository.list_versions(
            user_id, job_id, limit, offset
        )

        versions = [r.schema for r in resumes]
        return versions, total

    async def get_full_resume(
        self, version_id: uuid.UUID, user_id: Optional[uuid.UUID] = None
    ) -> Optional[FullResumeResponse]:
        """Get full resume with all sections."""
        resume = await self.uow.resume_repository.get_version(version_id, user_id)

        if not resume:
            return None

        # Get metadata
        metadata = None
        if resume.metadata_id:
            metadata_obj = await self.uow.resume_metadata_repository.get_by_id(
                resume.metadata_id, user_id
            )
            if metadata_obj:
                metadata = metadata_obj.schema

        # Get pinned sections
        educations = []
        if resume.pinned_education_ids:
            education_objs = await self.uow.resume_education_repository.get_by_ids(
                resume.pinned_education_ids, user_id
            )
            educations = [e.schema for e in education_objs]

        work_experiences = []
        if resume.pinned_experience_ids:
            work_objs = await self.uow.resume_work_experience_repository.get_by_ids(
                resume.pinned_experience_ids, user_id
            )
            work_experiences = [w.schema for w in work_objs]

        projects = []
        if resume.pinned_project_ids:
            project_objs = await self.uow.resume_project_repository.get_by_ids(
                resume.pinned_project_ids, user_id
            )
            projects = [p.schema for p in project_objs]

        skills = []
        if resume.pinned_skill_ids:
            skill_objs = await self.uow.resume_skill_repository.get_by_ids(
                resume.pinned_skill_ids, user_id
            )
            skills = [s.schema for s in skill_objs]

        return FullResumeResponse(
            version=resume.schema,
            metadata=metadata,
            educations=educations,
            work_experiences=work_experiences,
            projects=projects,
            skills=skills,
        )

    async def update_version_pins(
        self,
        version_id: uuid.UUID,
        user_id: uuid.UUID,
        metadata_id: Optional[uuid.UUID] = None,
        pinned_education_ids: Optional[List[uuid.UUID]] = None,
        pinned_experience_ids: Optional[List[uuid.UUID]] = None,
        pinned_project_ids: Optional[List[uuid.UUID]] = None,
        pinned_skill_ids: Optional[List[uuid.UUID]] = None,
    ) -> Optional[ResumeSchema]:
        """Update which sections are pinned to a resume version."""
        update_data = {}

        if metadata_id is not None:
            update_data["metadata_id"] = metadata_id
        if pinned_education_ids is not None:
            update_data["pinned_education_ids"] = pinned_education_ids
        if pinned_experience_ids is not None:
            update_data["pinned_experience_ids"] = pinned_experience_ids
        if pinned_project_ids is not None:
            update_data["pinned_project_ids"] = pinned_project_ids
        if pinned_skill_ids is not None:
            update_data["pinned_skill_ids"] = pinned_skill_ids

        resume = await self.uow.resume_repository.update_version(
            version_id, user_id, **update_data
        )

        if not resume:
            return None

        return resume.schema

    # Metadata operations
    async def get_metadata(
        self, metadata_id: uuid.UUID, user_id: Optional[uuid.UUID] = None
    ) -> Optional[ResumeMetadataSchema]:
        """Get resume metadata by ID."""
        metadata = await self.uow.resume_metadata_repository.get_by_id(
            metadata_id, user_id
        )

        if not metadata:
            return None

        return metadata.schema

    async def update_metadata(
        self, metadata_id: uuid.UUID, user_id: uuid.UUID, **kwargs
    ) -> Optional[ResumeMetadataSchema]:
        """Update resume metadata."""
        metadata = await self.uow.resume_metadata_repository.update(
            metadata_id, user_id, **kwargs
        )

        if not metadata:
            return None

        return metadata.schema

    async def enhance_metadata(
        self,
        metadata_id: uuid.UUID,
        user_id: uuid.UUID,
        request: AIEnhanceRequest,
    ) -> Optional[ResumeMetadataSchema]:
        """Enhance metadata using AI."""
        # Get current metadata
        metadata = await self.uow.resume_metadata_repository.get_by_id(
            metadata_id, user_id
        )
        if not metadata:
            return None

        # Create a fork for AI enhancement
        new_metadata = await self.uow.resume_metadata_repository.fork(
            metadata_id, user_id
        )
        if not new_metadata:
            return None

        # Use AI to enhance
        try:
            # This is a placeholder for actual AI enhancement
            # You would need to define proper response models for the instructor
            # The prompt would include current metadata and user request
            logger.info(
                f"AI enhancement requested for metadata {metadata_id} with prompt: {request.prompt}"
            )

            # For now, just return the forked metadata
            return new_metadata.schema

        except Exception as e:
            logger.error(f"Error enhancing metadata: {str(e)}")
            return None

    # Education operations
    async def get_education(
        self, education_id: uuid.UUID, user_id: Optional[uuid.UUID] = None
    ) -> Optional[ResumeEducationSchema]:
        """Get education by ID."""
        education = await self.uow.resume_education_repository.get_by_id(
            education_id, user_id
        )

        if not education:
            return None

        return education.schema

    async def update_education(
        self, education_id: uuid.UUID, user_id: uuid.UUID, **kwargs
    ) -> Optional[ResumeEducationSchema]:
        """Update education entry."""
        education = await self.uow.resume_education_repository.update(
            education_id, user_id, **kwargs
        )

        if not education:
            return None

        return education.schema

    async def enhance_education(
        self,
        education_id: uuid.UUID,
        user_id: uuid.UUID,
        request: AIEnhanceRequest,
    ) -> Optional[ResumeEducationSchema]:
        """Enhance education using AI."""
        # Get current education
        education = await self.uow.resume_education_repository.get_by_id(
            education_id, user_id
        )
        if not education:
            return None

        # Create a fork for AI enhancement
        new_education = await self.uow.resume_education_repository.fork(
            education_id, user_id
        )
        if not new_education:
            return None

        # AI enhancement logic would go here
        logger.info(f"AI enhancement requested for education {education_id}")

        return new_education.schema

    # Work experience operations
    async def get_work_experience(
        self, work_id: uuid.UUID, user_id: Optional[uuid.UUID] = None
    ) -> Optional[ResumeWorkExperienceSchema]:
        """Get work experience by ID."""
        work = await self.uow.resume_work_experience_repository.get_by_id(
            work_id, user_id
        )

        if not work:
            return None

        return work.schema

    async def update_work_experience(
        self, work_id: uuid.UUID, user_id: uuid.UUID, **kwargs
    ) -> Optional[ResumeWorkExperienceSchema]:
        """Update work experience entry."""
        work = await self.uow.resume_work_experience_repository.update(
            work_id, user_id, **kwargs
        )

        if not work:
            return None

        return work.schema

    async def enhance_work_experience(
        self,
        work_id: uuid.UUID,
        user_id: uuid.UUID,
        request: AIEnhanceRequest,
    ) -> Optional[ResumeWorkExperienceSchema]:
        """Enhance work experience using AI."""
        # Get current work experience
        work = await self.uow.resume_work_experience_repository.get_by_id(
            work_id, user_id
        )
        if not work:
            return None

        # Create a fork for AI enhancement
        new_work = await self.uow.resume_work_experience_repository.fork(
            work_id, user_id
        )
        if not new_work:
            return None

        # AI enhancement logic would go here
        logger.info(f"AI enhancement requested for work experience {work_id}")

        return new_work.schema

    # Project operations
    async def get_project(
        self, project_id: uuid.UUID, user_id: Optional[uuid.UUID] = None
    ) -> Optional[ResumeProjectSchema]:
        """Get project by ID."""
        project = await self.uow.resume_project_repository.get_by_id(
            project_id, user_id
        )

        if not project:
            return None

        return project.schema

    async def update_project(
        self, project_id: uuid.UUID, user_id: uuid.UUID, **kwargs
    ) -> Optional[ResumeProjectSchema]:
        """Update project entry."""
        project = await self.uow.resume_project_repository.update(
            project_id, user_id, **kwargs
        )

        if not project:
            return None

        return project.schema

    async def enhance_project(
        self,
        project_id: uuid.UUID,
        user_id: uuid.UUID,
        request: AIEnhanceRequest,
    ) -> Optional[ResumeProjectSchema]:
        """Enhance project using AI."""
        # Get current project
        project = await self.uow.resume_project_repository.get_by_id(
            project_id, user_id
        )
        if not project:
            return None

        # Create a fork for AI enhancement
        new_project = await self.uow.resume_project_repository.fork(project_id, user_id)
        if not new_project:
            return None

        # AI enhancement logic would go here
        logger.info(f"AI enhancement requested for project {project_id}")

        return new_project.schema

    # Skill operations
    async def get_skill(
        self, skill_id: uuid.UUID, user_id: Optional[uuid.UUID] = None
    ) -> Optional[ResumeSkillSchema]:
        """Get skill by ID."""
        skill = await self.uow.resume_skill_repository.get_by_id(skill_id, user_id)

        if not skill:
            return None

        return skill.schema

    async def update_skill(
        self, skill_id: uuid.UUID, user_id: uuid.UUID, **kwargs
    ) -> Optional[ResumeSkillSchema]:
        """Update skill entry."""
        skill = await self.uow.resume_skill_repository.update(
            skill_id, user_id, **kwargs
        )

        if not skill:
            return None

        return skill.schema

    async def enhance_skill(
        self,
        skill_id: uuid.UUID,
        user_id: uuid.UUID,
        request: AIEnhanceRequest,
    ) -> Optional[ResumeSkillSchema]:
        """Enhance skill using AI."""
        # Get current skill
        skill = await self.uow.resume_skill_repository.get_by_id(skill_id, user_id)
        if not skill:
            return None

        # Create a fork for AI enhancement
        new_skill = await self.uow.resume_skill_repository.fork(skill_id, user_id)
        if not new_skill:
            return None

        # AI enhancement logic would go here
        logger.info(f"AI enhancement requested for skill {skill_id}")

        return new_skill.schema
