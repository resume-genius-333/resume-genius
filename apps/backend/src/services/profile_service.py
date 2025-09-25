"""Service layer for managing user profile information."""

import logging
from typing import Optional
from uuid import UUID, uuid4

from src.core.unit_of_work import UnitOfWork
from src.models.api.profile import (
    EducationCreateRequest,
    EducationUpdateRequest,
    # EducationResponse,
    EducationListResponse,
    WorkExperienceCreateRequest,
    WorkExperienceUpdateRequest,
    WorkExperienceResponse,
    WorkExperienceListResponse,
    WorkResponsibilityRequest,
    WorkResponsibilityResponse,
    ProjectCreateRequest,
    ProjectUpdateRequest,
    ProjectResponse,
    ProjectListResponse,
    ProjectTaskRequest,
    ProjectTaskResponse,
)
from src.models.db.education import EducationSchema
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
    ) -> Optional[EducationSchema]:
        """Get all education entries for a user."""
        education = await self.uow.education_repository.get_education_by_id(
            education_id=education_id, user_id=user_id
        )
        return education

    async def create_education(
        self, user_id: UUID, request: EducationCreateRequest
    ) -> EducationSchema:
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
    ) -> Optional[EducationSchema]:
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

        # Fetch responsibilities for each work experience
        response_list = []
        for work in work_experiences:
            responsibilities = (
                await self.uow.work_repository.get_responsibilities_by_work(
                    work.id, user_id
                )
            )

            work_dict = work.model_dump()
            work_dict["responsibilities"] = [
                WorkResponsibilityResponse.model_validate(resp)
                for resp in responsibilities
            ]
            response_list.append(WorkExperienceResponse(**work_dict))

        return WorkExperienceListResponse(work_experiences=response_list, total=total)

    async def create_work_experience(
        self, user_id: UUID, request: WorkExperienceCreateRequest
    ) -> WorkExperienceResponse:
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

        work = await self.uow.work_repository.create_work_experience(
            user_id=user_id,
            work_id=work_id,
            llm_schema=llm_schema,
        )

        # Create responsibilities if provided
        responsibilities = []
        if request.responsibilities:
            for resp_desc in request.responsibilities:
                resp_id = uuid4()
                resp_llm = WorkResponsibilityLLMSchema(description=resp_desc)

                resp = await self.uow.work_repository.create_responsibility(
                    user_id=user_id,
                    work_id=work_id,
                    responsibility_id=resp_id,
                    llm_schema=resp_llm,
                )
                responsibilities.append(resp)

        await self.uow.commit()

        work_dict = work.model_dump()
        work_dict["responsibilities"] = [
            WorkResponsibilityResponse.model_validate(resp) for resp in responsibilities
        ]
        return WorkExperienceResponse(**work_dict)

    async def update_work_experience(
        self,
        user_id: UUID,
        work_id: UUID,
        request: WorkExperienceUpdateRequest,
    ) -> Optional[WorkExperienceResponse]:
        """Update a work experience entry."""
        update_data = request.model_dump(exclude_unset=True)

        work = await self.uow.work_repository.update_work_experience(
            work_id=work_id, user_id=user_id, **update_data
        )

        if not work:
            return None

        # Fetch responsibilities
        responsibilities = await self.uow.work_repository.get_responsibilities_by_work(
            work_id, user_id
        )

        await self.uow.commit()

        work_dict = work.model_dump()
        work_dict["responsibilities"] = [
            WorkResponsibilityResponse.model_validate(resp) for resp in responsibilities
        ]
        return WorkExperienceResponse(**work_dict)

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
    ) -> Optional[WorkResponsibilityResponse]:
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
        return WorkResponsibilityResponse.model_validate(responsibility)

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

        # Fetch tasks for each project
        response_list = []
        for project in projects:
            tasks = await self.uow.project_repository.get_tasks_by_project(
                project.id, user_id
            )

            project_dict = project.model_dump()
            project_dict["tasks"] = [
                ProjectTaskResponse.model_validate(task) for task in tasks
            ]
            response_list.append(ProjectResponse(**project_dict))

        return ProjectListResponse(projects=response_list, total=total)

    async def create_project(
        self, user_id: UUID, request: ProjectCreateRequest
    ) -> ProjectResponse:
        """Create a new project."""
        project_id = uuid4()

        # Create project
        llm_schema = ProjectLLMSchema(
            project_name=request.project_name,
            description=request.description,
            start_date=request.start_date,
            end_date=request.end_date,
            project_url=request.project_url,
            repository_url=request.repository_url,
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

        project_dict = project.model_dump()
        project_dict["tasks"] = [
            ProjectTaskResponse.model_validate(task) for task in tasks
        ]
        return ProjectResponse(**project_dict)

    async def update_project(
        self,
        user_id: UUID,
        project_id: UUID,
        request: ProjectUpdateRequest,
    ) -> Optional[ProjectResponse]:
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

        # Fetch tasks
        tasks = await self.uow.project_repository.get_tasks_by_project(
            project_id, user_id
        )

        await self.uow.commit()

        project_dict = project.model_dump()
        project_dict["tasks"] = [
            ProjectTaskResponse.model_validate(task) for task in tasks
        ]
        return ProjectResponse(**project_dict)

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
    ) -> Optional[ProjectTaskResponse]:
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
        return ProjectTaskResponse.model_validate(task)

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
