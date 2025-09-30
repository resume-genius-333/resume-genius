"""API router for user profile management endpoints."""

import logging
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from src.api.dependencies import get_current_user_id
from src.core.unit_of_work import UnitOfWorkFactory
from src.models.api.profile import (
    CreateProfileResumeUploadUrlRequest,
    CreateProfileResumeUploadUrlResponse,
    EducationCreateRequest,
    EducationUpdateRequest,
    EducationListResponse,
    StartProfileResumeExtractionRequest,
    StartProfileResumeExtractionResponse,
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
from src.services.profile_service import ProfileService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/profile", tags=["profile"])


# Education Endpoints
@router.get("/educations", response_model=EducationListResponse)
async def get_profile_educations(
    current_user_id: Annotated[UUID, Depends(get_current_user_id)],
):
    """Get all education entries for the current user."""
    async with UnitOfWorkFactory() as uow:
        profile_service = ProfileService(uow)
        return await profile_service.get_user_educations(current_user_id)


@router.get("/educations/{education_id}", response_model=ProfileEducationSchema)
async def get_profile_education(
    education_id: UUID,
    current_user_id: Annotated[UUID, Depends(get_current_user_id)],
):
    """Get all education entries for the current user."""
    async with UnitOfWorkFactory() as uow:
        profile_service = ProfileService(uow)
        return await profile_service.get_user_education(
            user_id=current_user_id, education_id=education_id
        )


@router.post(
    "/educations",
    response_model=ProfileEducationSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_profile_education(
    request: EducationCreateRequest,
    current_user_id: Annotated[UUID, Depends(get_current_user_id)],
):
    """Create a new education entry."""
    async with UnitOfWorkFactory() as uow:
        profile_service = ProfileService(uow)
        return await profile_service.create_education(current_user_id, request)


@router.put("/educations/{education_id}", response_model=ProfileEducationSchema)
async def update_profile_education(
    education_id: UUID,
    request: EducationUpdateRequest,
    current_user_id: Annotated[UUID, Depends(get_current_user_id)],
):
    """Update an education entry."""
    async with UnitOfWorkFactory() as uow:
        profile_service = ProfileService(uow)
        education = await profile_service.update_education(
            current_user_id, education_id, request
        )
        if not education:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Education entry not found",
            )
        return education


@router.delete("/educations/{education_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_profile_education(
    education_id: UUID,
    current_user_id: Annotated[UUID, Depends(get_current_user_id)],
):
    """Delete an education entry."""
    async with UnitOfWorkFactory() as uow:
        profile_service = ProfileService(uow)
        result = await profile_service.delete_education(current_user_id, education_id)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Education entry not found",
            )


# Work Experience Endpoints
@router.get("/work-experiences", response_model=WorkExperienceListResponse)
async def get_profile_work_experiences(
    current_user_id: Annotated[UUID, Depends(get_current_user_id)],
):
    """Get all work experiences for the current user."""
    async with UnitOfWorkFactory() as uow:
        profile_service = ProfileService(uow)
        return await profile_service.get_user_work_experiences(current_user_id)


@router.get("/work-experiences/{work_id}", response_model=ProfileWorkExperienceSchema)
async def get_profile_work_experience(
    work_id: UUID,
    current_user_id: Annotated[UUID, Depends(get_current_user_id)],
):
    """Get a single work experience entry by ID for the current user."""
    async with UnitOfWorkFactory() as uow:
        profile_service = ProfileService(uow)
        work_experience = await profile_service.get_user_work_experience_by_id(
            current_user_id, work_id
        )
        if not work_experience:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Work experience not found",
            )
        return work_experience


@router.post(
    "/work-experiences",
    response_model=ProfileWorkExperienceSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_profile_work_experience(
    request: WorkExperienceCreateRequest,
    current_user_id: Annotated[UUID, Depends(get_current_user_id)],
):
    """Create a new work experience entry."""
    async with UnitOfWorkFactory() as uow:
        profile_service = ProfileService(uow)
        return await profile_service.create_work_experience(current_user_id, request)


@router.put("/work-experiences/{work_id}", response_model=ProfileWorkExperienceSchema)
async def update_profile_work_experience(
    work_id: UUID,
    request: WorkExperienceUpdateRequest,
    current_user_id: Annotated[UUID, Depends(get_current_user_id)],
):
    """Update a work experience entry."""
    async with UnitOfWorkFactory() as uow:
        profile_service = ProfileService(uow)
        work_experience = await profile_service.update_work_experience(
            current_user_id, work_id, request
        )
        if not work_experience:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Work experience not found",
            )
        return work_experience


@router.delete("/work-experiences/{work_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_profile_work_experience(
    work_id: UUID,
    current_user_id: Annotated[UUID, Depends(get_current_user_id)],
):
    """Delete a work experience entry."""
    async with UnitOfWorkFactory() as uow:
        profile_service = ProfileService(uow)
        result = await profile_service.delete_work_experience(current_user_id, work_id)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Work experience not found",
            )


@router.post(
    "/work-experiences/{work_id}/responsibilities",
    response_model=ProfileWorkResponsibilitySchema,
    status_code=status.HTTP_201_CREATED,
)
async def add_profile_work_responsibility(
    work_id: UUID,
    request: WorkResponsibilityRequest,
    current_user_id: Annotated[UUID, Depends(get_current_user_id)],
):
    """Add a responsibility to a work experience."""
    async with UnitOfWorkFactory() as uow:
        profile_service = ProfileService(uow)
        responsibility = await profile_service.add_work_responsibility(
            current_user_id, work_id, request
        )
        if not responsibility:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Work experience not found",
            )
        return responsibility


@router.delete(
    "/work-experiences/{work_id}/responsibilities/{responsibility_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_profile_work_responsibility(
    work_id: UUID,
    responsibility_id: UUID,
    current_user_id: Annotated[UUID, Depends(get_current_user_id)],
):
    """Delete a responsibility from a work experience."""
    async with UnitOfWorkFactory() as uow:
        profile_service = ProfileService(uow)
        result = await profile_service.delete_work_responsibility(
            current_user_id, work_id, responsibility_id
        )
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Responsibility not found"
            )


# Project Endpoints
@router.get("/projects", response_model=ProjectListResponse)
async def get_profile_projects(
    current_user_id: Annotated[UUID, Depends(get_current_user_id)],
):
    """Get all projects for the current user."""
    async with UnitOfWorkFactory() as uow:
        profile_service = ProfileService(uow)
        return await profile_service.get_user_projects(current_user_id)


@router.get("/projects/{project_id}", response_model=ProfileProjectSchema)
async def get_profile_project(
    project_id: UUID,
    current_user_id: Annotated[UUID, Depends(get_current_user_id)],
):
    """Get a single project for the current user."""
    async with UnitOfWorkFactory() as uow:
        profile_service = ProfileService(uow)
        project = await profile_service.get_user_project(current_user_id, project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
            )
        return project


@router.post(
    "/projects",
    response_model=ProfileProjectSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_profile_project(
    request: ProjectCreateRequest,
    current_user_id: Annotated[UUID, Depends(get_current_user_id)],
):
    """Create a new project."""
    async with UnitOfWorkFactory() as uow:
        profile_service = ProfileService(uow)
        return await profile_service.create_project(current_user_id, request)


@router.put("/projects/{project_id}", response_model=ProfileProjectSchema)
async def update_profile_project(
    project_id: UUID,
    request: ProjectUpdateRequest,
    current_user_id: Annotated[UUID, Depends(get_current_user_id)],
):
    """Update a project."""
    async with UnitOfWorkFactory() as uow:
        profile_service = ProfileService(uow)
        project = await profile_service.update_project(
            current_user_id, project_id, request
        )
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
            )
        return project


@router.delete("/projects/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_profile_project(
    project_id: UUID,
    current_user_id: Annotated[UUID, Depends(get_current_user_id)],
):
    """Delete a project."""
    async with UnitOfWorkFactory() as uow:
        profile_service = ProfileService(uow)
        result = await profile_service.delete_project(current_user_id, project_id)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
            )


@router.post(
    "/projects/{project_id}/tasks",
    response_model=ProfileProjectTaskSchema,
    status_code=status.HTTP_201_CREATED,
)
async def add_profile_project_task(
    project_id: UUID,
    request: ProjectTaskRequest,
    current_user_id: Annotated[UUID, Depends(get_current_user_id)],
):
    """Add a task to a project."""
    async with UnitOfWorkFactory() as uow:
        profile_service = ProfileService(uow)
        task = await profile_service.add_project_task(
            current_user_id, project_id, request
        )
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
            )
        return task


@router.delete(
    "/projects/{project_id}/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_profile_project_task(
    project_id: UUID,
    task_id: UUID,
    current_user_id: Annotated[UUID, Depends(get_current_user_id)],
):
    """Delete a task from a project."""
    async with UnitOfWorkFactory() as uow:
        profile_service = ProfileService(uow)
        result = await profile_service.delete_project_task(
            current_user_id, project_id, task_id
        )
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
            )


@router.post(
    "/profile-resume/upload/", response_model=CreateProfileResumeUploadUrlResponse
)
async def create_profile_resume_upload_url(
    request: CreateProfileResumeUploadUrlRequest,
    current_user_id: Annotated[UUID, Depends(get_current_user_id)],
):
    raise NotImplementedError()


@router.post(
    "/profile-resume/extract/{resume_id}",
    response_model=StartProfileResumeExtractionResponse,
)
async def start_profile_resume_extraction(
    resume_id: UUID,
    request: StartProfileResumeExtractionRequest,
    current_user_id: Annotated[UUID, Depends(get_current_user_id)],
):
    raise NotImplementedError()
