"""Service for resume-related business logic."""

from typing import Optional, List
import uuid
import logging
from instructor import AsyncInstructor

from src.repositories.resume_repository import (
    ResumeRepository,
    ResumeMetadataRepository,
    ResumeEducationRepository,
    ResumeWorkExperienceRepository,
    ResumeProjectRepository,
    ResumeSkillRepository,
)
from src.models.api.resume import (
    ResumeVersionResponse,
    ResumeMetadataResponse,
    ResumeEducationResponse,
    ResumeWorkExperienceResponse,
    ResumeProjectResponse,
    ResumeSkillResponse,
    FullResumeResponse,
    AIEnhanceRequest,
)

logger = logging.getLogger(__name__)


class ResumeService:
    """Service for resume business logic."""

    def __init__(
        self,
        resume_repo: ResumeRepository,
        metadata_repo: ResumeMetadataRepository,
        education_repo: ResumeEducationRepository,
        work_repo: ResumeWorkExperienceRepository,
        project_repo: ResumeProjectRepository,
        skill_repo: ResumeSkillRepository,
        instructor: AsyncInstructor,
    ):
        """Initialize resume service with dependencies."""
        self.resume_repo = resume_repo
        self.metadata_repo = metadata_repo
        self.education_repo = education_repo
        self.work_repo = work_repo
        self.project_repo = project_repo
        self.skill_repo = skill_repo
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
    ) -> ResumeVersionResponse:
        """Create a new resume version."""
        resume = await self.resume_repo.create_version(
            user_id=user_id,
            job_id=job_id,
            metadata_id=metadata_id,
            parent_version=parent_version,
            pinned_education_ids=pinned_education_ids,
            pinned_experience_ids=pinned_experience_ids,
            pinned_project_ids=pinned_project_ids,
            pinned_skill_ids=pinned_skill_ids,
        )

        return self._to_version_response(resume)

    async def get_version(
        self, version_id: uuid.UUID, user_id: Optional[uuid.UUID] = None
    ) -> Optional[ResumeVersionResponse]:
        """Get a resume version by ID."""
        resume = await self.resume_repo.get_version(version_id, user_id)

        if not resume:
            return None

        return self._to_version_response(resume)

    async def get_latest_version(
        self, user_id: uuid.UUID, job_id: Optional[uuid.UUID] = None
    ) -> Optional[ResumeVersionResponse]:
        """Get the latest resume version for a user."""
        resume = await self.resume_repo.get_latest_version(user_id, job_id)

        if not resume:
            return None

        return self._to_version_response(resume)

    async def list_versions(
        self,
        user_id: uuid.UUID,
        job_id: Optional[uuid.UUID] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[List[ResumeVersionResponse], int]:
        """List resume versions with pagination."""
        resumes, total = await self.resume_repo.list_versions(
            user_id, job_id, limit, offset
        )

        versions = [self._to_version_response(r) for r in resumes]
        return versions, total

    async def get_full_resume(
        self, version_id: uuid.UUID, user_id: Optional[uuid.UUID] = None
    ) -> Optional[FullResumeResponse]:
        """Get full resume with all sections."""
        resume = await self.resume_repo.get_version(version_id, user_id)

        if not resume:
            return None

        # Get metadata
        metadata = None
        if resume.metadata_id:
            metadata_obj = await self.metadata_repo.get_by_id(
                resume.metadata_id, user_id
            )
            if metadata_obj:
                metadata = self._to_metadata_response(metadata_obj)

        # Get pinned sections
        educations = []
        if resume.pinned_education_ids:
            education_objs = await self.education_repo.get_by_ids(
                resume.pinned_education_ids, user_id
            )
            educations = [self._to_education_response(e) for e in education_objs]

        work_experiences = []
        if resume.pinned_experience_ids:
            work_objs = await self.work_repo.get_by_ids(
                resume.pinned_experience_ids, user_id
            )
            work_experiences = [self._to_work_response(w) for w in work_objs]

        projects = []
        if resume.pinned_project_ids:
            project_objs = await self.project_repo.get_by_ids(
                resume.pinned_project_ids, user_id
            )
            projects = [self._to_project_response(p) for p in project_objs]

        skills = []
        if resume.pinned_skill_ids:
            skill_objs = await self.skill_repo.get_by_ids(
                resume.pinned_skill_ids, user_id
            )
            skills = [self._to_skill_response(s) for s in skill_objs]

        return FullResumeResponse(
            version=self._to_version_response(resume),
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
    ) -> Optional[ResumeVersionResponse]:
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

        resume = await self.resume_repo.update_version(version_id, user_id, **update_data)

        if not resume:
            return None

        return self._to_version_response(resume)

    # Metadata operations
    async def get_metadata(
        self, metadata_id: uuid.UUID, user_id: Optional[uuid.UUID] = None
    ) -> Optional[ResumeMetadataResponse]:
        """Get resume metadata by ID."""
        metadata = await self.metadata_repo.get_by_id(metadata_id, user_id)

        if not metadata:
            return None

        return self._to_metadata_response(metadata)

    async def update_metadata(
        self, metadata_id: uuid.UUID, user_id: uuid.UUID, **kwargs
    ) -> Optional[ResumeMetadataResponse]:
        """Update resume metadata."""
        metadata = await self.metadata_repo.update(metadata_id, user_id, **kwargs)

        if not metadata:
            return None

        return self._to_metadata_response(metadata)

    async def enhance_metadata(
        self,
        metadata_id: uuid.UUID,
        user_id: uuid.UUID,
        request: AIEnhanceRequest,
    ) -> Optional[ResumeMetadataResponse]:
        """Enhance metadata using AI."""
        # Get current metadata
        metadata = await self.metadata_repo.get_by_id(metadata_id, user_id)
        if not metadata:
            return None

        # Create a fork for AI enhancement
        new_metadata = await self.metadata_repo.fork(metadata_id, user_id)
        if not new_metadata:
            return None

        # Use AI to enhance
        try:
            # This is a placeholder for actual AI enhancement
            # You would need to define proper response models for the instructor
            # The prompt would include current metadata and user request
            logger.info(f"AI enhancement requested for metadata {metadata_id} with prompt: {request.prompt}")

            # For now, just return the forked metadata
            return self._to_metadata_response(new_metadata)

        except Exception as e:
            logger.error(f"Error enhancing metadata: {str(e)}")
            return None

    # Education operations
    async def get_education(
        self, education_id: uuid.UUID, user_id: Optional[uuid.UUID] = None
    ) -> Optional[ResumeEducationResponse]:
        """Get education by ID."""
        education = await self.education_repo.get_by_id(education_id, user_id)

        if not education:
            return None

        return self._to_education_response(education)

    async def update_education(
        self, education_id: uuid.UUID, user_id: uuid.UUID, **kwargs
    ) -> Optional[ResumeEducationResponse]:
        """Update education entry."""
        education = await self.education_repo.update(education_id, user_id, **kwargs)

        if not education:
            return None

        return self._to_education_response(education)

    async def enhance_education(
        self,
        education_id: uuid.UUID,
        user_id: uuid.UUID,
        request: AIEnhanceRequest,
    ) -> Optional[ResumeEducationResponse]:
        """Enhance education using AI."""
        # Get current education
        education = await self.education_repo.get_by_id(education_id, user_id)
        if not education:
            return None

        # Create a fork for AI enhancement
        new_education = await self.education_repo.fork(education_id, user_id)
        if not new_education:
            return None

        # AI enhancement logic would go here
        logger.info(f"AI enhancement requested for education {education_id}")

        return self._to_education_response(new_education)

    # Work experience operations
    async def get_work_experience(
        self, work_id: uuid.UUID, user_id: Optional[uuid.UUID] = None
    ) -> Optional[ResumeWorkExperienceResponse]:
        """Get work experience by ID."""
        work = await self.work_repo.get_by_id(work_id, user_id)

        if not work:
            return None

        return self._to_work_response(work)

    async def update_work_experience(
        self, work_id: uuid.UUID, user_id: uuid.UUID, **kwargs
    ) -> Optional[ResumeWorkExperienceResponse]:
        """Update work experience entry."""
        work = await self.work_repo.update(work_id, user_id, **kwargs)

        if not work:
            return None

        return self._to_work_response(work)

    async def enhance_work_experience(
        self,
        work_id: uuid.UUID,
        user_id: uuid.UUID,
        request: AIEnhanceRequest,
    ) -> Optional[ResumeWorkExperienceResponse]:
        """Enhance work experience using AI."""
        # Get current work experience
        work = await self.work_repo.get_by_id(work_id, user_id)
        if not work:
            return None

        # Create a fork for AI enhancement
        new_work = await self.work_repo.fork(work_id, user_id)
        if not new_work:
            return None

        # AI enhancement logic would go here
        logger.info(f"AI enhancement requested for work experience {work_id}")

        return self._to_work_response(new_work)

    # Project operations
    async def get_project(
        self, project_id: uuid.UUID, user_id: Optional[uuid.UUID] = None
    ) -> Optional[ResumeProjectResponse]:
        """Get project by ID."""
        project = await self.project_repo.get_by_id(project_id, user_id)

        if not project:
            return None

        return self._to_project_response(project)

    async def update_project(
        self, project_id: uuid.UUID, user_id: uuid.UUID, **kwargs
    ) -> Optional[ResumeProjectResponse]:
        """Update project entry."""
        project = await self.project_repo.update(project_id, user_id, **kwargs)

        if not project:
            return None

        return self._to_project_response(project)

    async def enhance_project(
        self,
        project_id: uuid.UUID,
        user_id: uuid.UUID,
        request: AIEnhanceRequest,
    ) -> Optional[ResumeProjectResponse]:
        """Enhance project using AI."""
        # Get current project
        project = await self.project_repo.get_by_id(project_id, user_id)
        if not project:
            return None

        # Create a fork for AI enhancement
        new_project = await self.project_repo.fork(project_id, user_id)
        if not new_project:
            return None

        # AI enhancement logic would go here
        logger.info(f"AI enhancement requested for project {project_id}")

        return self._to_project_response(new_project)

    # Skill operations
    async def get_skill(
        self, skill_id: uuid.UUID, user_id: Optional[uuid.UUID] = None
    ) -> Optional[ResumeSkillResponse]:
        """Get skill by ID."""
        skill = await self.skill_repo.get_by_id(skill_id, user_id)

        if not skill:
            return None

        return self._to_skill_response(skill)

    async def update_skill(
        self, skill_id: uuid.UUID, user_id: uuid.UUID, **kwargs
    ) -> Optional[ResumeSkillResponse]:
        """Update skill entry."""
        skill = await self.skill_repo.update(skill_id, user_id, **kwargs)

        if not skill:
            return None

        return self._to_skill_response(skill)

    async def enhance_skill(
        self,
        skill_id: uuid.UUID,
        user_id: uuid.UUID,
        request: AIEnhanceRequest,
    ) -> Optional[ResumeSkillResponse]:
        """Enhance skill using AI."""
        # Get current skill
        skill = await self.skill_repo.get_by_id(skill_id, user_id)
        if not skill:
            return None

        # Create a fork for AI enhancement
        new_skill = await self.skill_repo.fork(skill_id, user_id)
        if not new_skill:
            return None

        # AI enhancement logic would go here
        logger.info(f"AI enhancement requested for skill {skill_id}")

        return self._to_skill_response(new_skill)

    # Helper methods to convert DB models to response models
    def _to_version_response(self, resume) -> ResumeVersionResponse:
        """Convert Resume DB model to response model."""
        return ResumeVersionResponse(
            version=resume.version,
            user_id=resume.user_id,
            job_id=resume.job_id,
            parent_version=resume.parent_version,
            metadata_id=resume.metadata_id,
            pinned_education_ids=resume.pinned_education_ids or [],
            pinned_experience_ids=resume.pinned_experience_ids or [],
            pinned_project_ids=resume.pinned_project_ids or [],
            pinned_skill_ids=resume.pinned_skill_ids or [],
            created_at=resume.created_at,
            updated_at=resume.updated_at,
        )

    def _to_metadata_response(self, metadata) -> ResumeMetadataResponse:
        """Convert ResumeMetadata DB model to response model."""
        return ResumeMetadataResponse(
            id=metadata.id,
            user_id=metadata.user_id,
            job_id=metadata.job_id,
            parent_id=metadata.parent_id,
            user_name=metadata.user_name,
            email=metadata.email,
            phone=metadata.phone,
            location=metadata.location,
            linkedin_url=metadata.linkedin_url,
            github_url=metadata.github_url,
            portfolio_website=metadata.portfolio_website,
            custom_styles=metadata.custom_styles,
            created_at=metadata.created_at,
            updated_at=metadata.updated_at,
        )

    def _to_education_response(self, education) -> ResumeEducationResponse:
        """Convert ResumeEducation DB model to response model."""
        return ResumeEducationResponse(
            id=education.id,
            user_id=education.user_id,
            job_id=education.job_id,
            parent_id=education.parent_id,
            institution_name=education.institution_name,
            degree=education.degree,
            field_of_study=education.field_of_study,
            focus_area=education.focus_area,
            start_date=education.start_date,
            end_date=education.end_date,
            gpa=education.gpa,
            max_gpa=education.max_gpa,
            city=education.city,
            country=education.country,
            created_at=education.created_at,
            updated_at=education.updated_at,
        )

    def _to_work_response(self, work) -> ResumeWorkExperienceResponse:
        """Convert ResumeWorkExperience DB model to response model."""
        # Note: The DB model doesn't have description and achievements fields
        # You may need to add these to the DB model or handle them differently
        return ResumeWorkExperienceResponse(
            id=work.id,
            user_id=work.user_id,
            job_id=work.job_id,
            parent_id=work.parent_id,
            job_title=work.job_title,
            company_name=work.company_name,
            employment_type=work.employment_type,
            start_date=work.start_date,
            end_date=work.end_date,
            location=work.location,
            description=None,  # Add this field to DB model if needed
            achievements=None,  # Add this field to DB model if needed
            created_at=work.created_at,
            updated_at=work.updated_at,
        )

    def _to_project_response(self, project) -> ResumeProjectResponse:
        """Convert ResumeProject DB model to response model."""
        # Note: The DB model doesn't have technologies and url fields
        # You may need to add these to the DB model or handle them differently
        return ResumeProjectResponse(
            id=project.id,
            user_id=project.user_id,
            job_id=project.job_id,
            parent_id=project.parent_id,
            project_name=project.project_name,
            role=project.role,
            start_date=project.start_date,
            end_date=project.end_date,
            location=project.location,
            description=project.description,
            technologies=None,  # Add this field to DB model if needed
            url=None,  # Add this field to DB model if needed
            created_at=project.created_at,
            updated_at=project.updated_at,
        )

    def _to_skill_response(self, skill) -> ResumeSkillResponse:
        """Convert ResumeSkill DB model to response model."""
        # Note: The DB model doesn't have years_of_experience field
        # You may need to add this to the DB model or handle it differently
        return ResumeSkillResponse(
            id=skill.id,
            user_id=skill.user_id,
            job_id=skill.job_id,
            parent_id=skill.parent_id,
            skill_name=skill.skill_name,
            skill_category=skill.skill_category,
            proficiency_level=skill.proficiency_level,
            years_of_experience=None,  # Add this field to DB model if needed
            created_at=skill.created_at,
            updated_at=skill.updated_at,
        )