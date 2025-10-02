"""Service layer for managing user profile information."""

import logging
from typing import Optional
from uuid import UUID, uuid4

from pydantic import HttpUrl

from src.core.unit_of_work import UnitOfWork
from src.models.api.profile import (
    EducationCreateRequest,
    EducationUpdateRequest,
    # EducationResponse,
    EducationListResponse,
    WorkExperienceCreateRequest,
    WorkExperienceUpdateRequest,
    WorkExperienceListResponse,
    WorkResponsibilityRequest,
    ProjectCreateRequest,
    ProjectUpdateRequest,
    ProjectListResponse,
    ProjectTaskRequest,
)
from src.models.db.profile import (
    ProfileEducationSchema,
    ProfileProjectSchema,
    ProfileProjectTaskSchema,
    ProfileWorkExperienceSchema,
    ProfileWorkResponsibilitySchema,
)
from src.models.llm.education import EducationLLMSchema
from src.models.llm.work import WorkExperienceLLMSchema, WorkResponsibilityLLMSchema
from src.models.llm.project import ProjectLLMSchema, ProjectTaskLLMSchema

logger = logging.getLogger(__name__)


class ProfileService:
    """Service for managing user profile information."""

    def __init__(self, uow: UnitOfWork):
        """Initialize the profile service."""
        self.uow = uow

    # Education Methods
    async def get_user_educations(self, user_id: UUID) -> EducationListResponse:
        """Get all education entries for a user."""
        educations = await self.uow.education_repository.get_educations_by_user(user_id)
        total = await self.uow.education_repository.get_educations_count(user_id)

        return EducationListResponse(
            educations=educations,
            total=total,
        )

    async def get_user_education(
        self, user_id: UUID, education_id: UUID
    ) -> Optional[ProfileEducationSchema]:
        """Get all education entries for a user."""
        education = await self.uow.education_repository.get_education_by_id(
            education_id=education_id, user_id=user_id
        )
        return education

    async def create_education(
        self, user_id: UUID, request: EducationCreateRequest
    ) -> ProfileEducationSchema:
        """Create a new education entry."""
        education_id = uuid4()

        # Convert to LLM schema
        llm_schema = EducationLLMSchema(
            institution_name=request.institution_name,
            degree=request.degree,
            field_of_study=request.field_of_study,
            focus_area=request.focus_area,
            start_date=request.start_date,
            end_date=request.end_date,
            gpa=request.gpa,
            max_gpa=request.max_gpa,
        )

        education = await self.uow.education_repository.create_education(
            user_id=user_id,
            education_id=education_id,
            llm_schema=llm_schema,
        )

        await self.uow.commit()
        return education

    async def update_education(
        self,
        user_id: UUID,
        education_id: UUID,
        request: EducationUpdateRequest,
    ) -> Optional[ProfileEducationSchema]:
        """Update an education entry."""
        update_data = request.model_dump(exclude_unset=True)

        education = await self.uow.education_repository.update_education(
            education_id=education_id, user_id=user_id, **update_data
        )

        if not education:
            return None

        await self.uow.commit()
        return education

    async def delete_education(self, user_id: UUID, education_id: UUID) -> bool:
        """Delete an education entry."""
        result = await self.uow.education_repository.delete_education(
            education_id=education_id, user_id=user_id
        )

        if result:
            await self.uow.commit()
        return result

    # Work Experience Methods
    async def get_user_work_experiences(
        self, user_id: UUID
    ) -> WorkExperienceListResponse:
        """Get all work experiences for a user."""
        work_experiences = await self.uow.work_repository.get_work_experiences_by_user(
            user_id
        )
        total = await self.uow.work_repository.get_work_experiences_count(user_id)

        return WorkExperienceListResponse(
            work_experiences=work_experiences, total=total
        )

    async def get_user_work_experience_by_id(
        self, user_id: UUID, work_id: UUID
    ) -> Optional[ProfileWorkExperienceSchema]:
        """Get a single work experience by ID for a user."""
        work_experience = await self.uow.work_repository.get_work_experience_by_id(
            work_id=work_id, user_id=user_id
        )
        return work_experience

    async def create_work_experience(
        self, user_id: UUID, request: WorkExperienceCreateRequest
    ) -> ProfileWorkExperienceSchema:
        """Create a new work experience entry."""
        work_id = uuid4()

        # Create work experience
        llm_schema = WorkExperienceLLMSchema(
            company_name=request.company_name,
            position_title=request.position_title,
            employment_type=request.employment_type,
            location=request.location,
            start_date=request.start_date,
            end_date=request.end_date,
        )

        await self.uow.work_repository.create_work_experience(
            user_id=user_id,
            work_id=work_id,
            llm_schema=llm_schema,
        )

        # Create responsibilities if provided
        if request.responsibilities:
            for resp_desc in request.responsibilities:
                resp_id = uuid4()
                resp_llm = WorkResponsibilityLLMSchema(description=resp_desc)

                await self.uow.work_repository.create_responsibility(
                    user_id=user_id,
                    work_id=work_id,
                    responsibility_id=resp_id,
                    llm_schema=resp_llm,
                )

        await self.uow.commit()

        work_with_responsibilities = (
            await self.uow.work_repository.get_work_experience_by_id(
                work_id=work_id, user_id=user_id
            )
        )

        if not work_with_responsibilities:
            raise RuntimeError(
                "Failed to load newly created work experience for response"
            )

        return work_with_responsibilities

    async def update_work_experience(
        self,
        user_id: UUID,
        work_id: UUID,
        request: WorkExperienceUpdateRequest,
    ) -> Optional[ProfileWorkExperienceSchema]:
        """Update a work experience entry."""
        update_data = request.model_dump(exclude_unset=True)

        work = await self.uow.work_repository.update_work_experience(
            work_id=work_id, user_id=user_id, **update_data
        )

        if not work:
            return None

        await self.uow.commit()

        return work

    async def delete_work_experience(self, user_id: UUID, work_id: UUID) -> bool:
        """Delete a work experience entry."""
        result = await self.uow.work_repository.delete_work_experience(
            work_id=work_id, user_id=user_id
        )

        if result:
            await self.uow.commit()
        return result

    async def add_work_responsibility(
        self,
        user_id: UUID,
        work_id: UUID,
        request: WorkResponsibilityRequest,
    ) -> Optional[ProfileWorkResponsibilitySchema]:
        """Add a responsibility to a work experience."""
        # Verify work experience exists
        work = await self.uow.work_repository.get_work_experience_by_id(
            work_id, user_id
        )
        if not work:
            return None

        resp_id = uuid4()
        resp_llm = WorkResponsibilityLLMSchema(description=request.description)

        responsibility = await self.uow.work_repository.create_responsibility(
            user_id=user_id,
            work_id=work_id,
            responsibility_id=resp_id,
            llm_schema=resp_llm,
        )

        await self.uow.commit()
        return responsibility

    async def delete_work_responsibility(
        self, user_id: UUID, work_id: UUID, responsibility_id: UUID
    ) -> bool:
        """Delete a work responsibility."""
        # Verify the responsibility belongs to this work experience
        resp = await self.uow.work_repository.get_responsibility_by_id(
            responsibility_id, user_id
        )

        if not resp or resp.work_id != work_id:
            return False

        result = await self.uow.work_repository.delete_responsibility(
            responsibility_id=responsibility_id, user_id=user_id
        )

        if result:
            await self.uow.commit()
        return result

    # Project Methods
    async def get_user_projects(self, user_id: UUID) -> ProjectListResponse:
        """Get all projects for a user."""
        projects = await self.uow.project_repository.get_projects_by_user(user_id)
        total = await self.uow.project_repository.get_projects_count(user_id)
        return ProjectListResponse(projects=projects, total=total)

    async def get_user_project(
        self, user_id: UUID, project_id: UUID
    ) -> Optional[ProfileProjectSchema]:
        """Get a single project by ID for a user."""
        project = await self.uow.project_repository.get_project_by_id(
            project_id=project_id, user_id=user_id
        )
        return project

    async def create_project(
        self, user_id: UUID, request: ProjectCreateRequest
    ) -> ProfileProjectSchema:
        """Create a new project."""
        project_id = uuid4()

        # Create project
        llm_schema = ProjectLLMSchema(
            project_name=request.project_name,
            description=request.description,
            start_date=request.start_date,
            end_date=request.end_date,
            project_url=HttpUrl(request.project_url) if request.project_url else None,
            repository_url=HttpUrl(request.repository_url)
            if request.repository_url
            else None,
        )

        project = await self.uow.project_repository.create_project(
            user_id=user_id,
            project_id=project_id,
            llm_schema=llm_schema,
        )

        # Create tasks if provided
        tasks = []
        if request.tasks:
            for task_desc in request.tasks:
                task_id = uuid4()
                task_llm = ProjectTaskLLMSchema(description=task_desc)

                task = await self.uow.project_repository.create_task(
                    user_id=user_id,
                    project_id=project_id,
                    task_id=task_id,
                    llm_schema=task_llm,
                )
                tasks.append(task)

        await self.uow.commit()

        return project

    async def update_project(
        self,
        user_id: UUID,
        project_id: UUID,
        request: ProjectUpdateRequest,
    ) -> Optional[ProfileProjectSchema]:
        """Update a project."""
        update_data = request.model_dump(exclude_unset=True)

        # Convert URLs to strings if present
        if "project_url" in update_data and update_data["project_url"]:
            update_data["project_url"] = str(update_data["project_url"])
        if "repository_url" in update_data and update_data["repository_url"]:
            update_data["repository_url"] = str(update_data["repository_url"])

        project = await self.uow.project_repository.update_project(
            project_id=project_id, user_id=user_id, **update_data
        )

        if not project:
            return None

        await self.uow.commit()

        return project

    async def delete_project(self, user_id: UUID, project_id: UUID) -> bool:
        """Delete a project."""
        result = await self.uow.project_repository.delete_project(
            project_id=project_id, user_id=user_id
        )

        if result:
            await self.uow.commit()
        return result

    async def add_project_task(
        self,
        user_id: UUID,
        project_id: UUID,
        request: ProjectTaskRequest,
    ) -> Optional[ProfileProjectTaskSchema]:
        """Add a task to a project."""
        # Verify project exists
        project = await self.uow.project_repository.get_project_by_id(
            project_id, user_id
        )
        if not project:
            return None

        task_id = uuid4()
        task_llm = ProjectTaskLLMSchema(description=request.description)

        task = await self.uow.project_repository.create_task(
            user_id=user_id,
            project_id=project_id,
            task_id=task_id,
            llm_schema=task_llm,
        )

        await self.uow.commit()
        return task

    async def delete_project_task(
        self, user_id: UUID, project_id: UUID, task_id: UUID
    ) -> bool:
        """Delete a project task."""
        # Verify the task belongs to this project
        task = await self.uow.project_repository.get_task_by_id(task_id, user_id)

        if not task or task.project_id != project_id:
            return False

        result = await self.uow.project_repository.delete_task(
            task_id=task_id, user_id=user_id
        )

        if result:
            await self.uow.commit()
        return result
