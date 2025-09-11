"""Resume router with comprehensive CRUD and AI enhancement endpoints."""

import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from dependency_injector.wiring import inject, Provide

from src.api.dependencies import get_current_user
from src.containers import Container
from src.core.unit_of_work import UnitOfWorkFactory
from src.models.auth.user import UserResponse
from src.models.api.resume import (
    PaginatedResponse,
    AIEnhanceRequest,
    ResumeVersionResponse,
    ResumeMetadataRequest,
    ResumeMetadataResponse,
    ResumeEducationRequest,
    ResumeEducationResponse,
    ResumeWorkExperienceRequest,
    ResumeWorkExperienceResponse,
    ResumeProjectRequest,
    ResumeProjectResponse,
    ResumeSkillRequest,
    ResumeSkillResponse,
    FullResumeResponse,
    CreateResumeVersionRequest,
    UpdateResumeVersionRequest,
)
from src.services.resume_service import ResumeService
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# ==================== Resume Version Endpoints ====================


@router.get("/resumes/", response_model=PaginatedResponse)
@inject
async def list_resume_versions(
    job_id: Optional[uuid.UUID] = None,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: UserResponse = Depends(get_current_user),
    instructor=Depends(Provide[Container.async_instructor]),
):
    """List all resume versions for the current user with pagination."""
    user_id = uuid.UUID(current_user.id)
    async with UnitOfWorkFactory() as uow:
        service = ResumeService(uow, instructor)
        versions, total = await service.list_versions(user_id, job_id, limit, offset)

        return PaginatedResponse(
            items=versions,
            total=total,
            limit=limit,
            offset=offset,
            has_more=(offset + limit) < total,
        )


@router.get("/resumes/latest", response_model=ResumeVersionResponse)
@inject
async def get_latest_resume_version(
    job_id: Optional[uuid.UUID] = None,
    current_user: UserResponse = Depends(get_current_user),
    instructor=Depends(Provide[Container.async_instructor]),
):
    """Get the latest resume version for the current user."""
    user_id = uuid.UUID(current_user.id)
    async with UnitOfWorkFactory() as uow:
        service = ResumeService(uow, instructor)
        version = await service.get_latest_version(user_id, job_id)

        if not version:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No resume versions found",
            )

        return version


@router.post("/resumes/", response_model=ResumeVersionResponse)
@inject
async def create_resume_version(
    request: CreateResumeVersionRequest,
    current_user: UserResponse = Depends(get_current_user),
    instructor=Depends(Provide[Container.async_instructor]),
):
    """Create a new resume version."""
    user_id = uuid.UUID(current_user.id)

    if not request.metadata_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="metadata_id is required",
        )

    async with UnitOfWorkFactory() as uow:
        service = ResumeService(uow, instructor)
        version = await service.create_version(
            user_id=user_id,
            job_id=request.job_id,
            metadata_id=request.metadata_id,
            parent_version=request.parent_version,
            pinned_education_ids=request.pinned_education_ids,
            pinned_experience_ids=request.pinned_experience_ids,
            pinned_project_ids=request.pinned_project_ids,
            pinned_skill_ids=request.pinned_skill_ids,
        )
        await uow.commit()
        return version


@router.get("/resumes/{version_id}", response_model=FullResumeResponse)
async def get_full_resume(
    version_id: uuid.UUID,
    current_user: UserResponse = Depends(get_current_user),
):
    """Get full resume with all sections for a specific version."""
    user_id = uuid.UUID(current_user.id)
    async with UnitOfWorkFactory() as uow:
        service = ResumeService(uow)
        resume = await service.get_full_resume(version_id, user_id)

    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume version not found",
        )
    return resume


@router.put("/resumes/{version_id}", response_model=ResumeVersionResponse)
async def update_resume_version(
    version_id: uuid.UUID,
    request: UpdateResumeVersionRequest,
    current_user: UserResponse = Depends(get_current_user),
):
    """Update which sections are pinned to a resume version."""
    user_id = uuid.UUID(current_user.id)
    async with UnitOfWorkFactory() as uow:
        service = ResumeService(uow)
        version = await service.update_version_pins(
            version_id=version_id,
            user_id=user_id,
            metadata_id=request.metadata_id,
            pinned_education_ids=request.pinned_education_ids,
            pinned_experience_ids=request.pinned_experience_ids,
            pinned_project_ids=request.pinned_project_ids,
            pinned_skill_ids=request.pinned_skill_ids,
        )

    if not version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume version not found",
        )

    return version


@router.post("/resumes/{version_id}/enhance", response_model=ResumeVersionResponse)
async def enhance_resume_version(
    version_id: uuid.UUID,
    request: AIEnhanceRequest,
    current_user: UserResponse = Depends(get_current_user),
):
    """Enhance entire resume version using AI."""
    user_id = uuid.UUID(current_user.id)

    # This would trigger a comprehensive AI enhancement of the entire resume
    # Implementation would involve creating new versions of all sections
    logger.info(f"AI enhancement requested for resume version {version_id}")
    async with UnitOfWorkFactory() as uow:
        service = ResumeService(uow)
        version = await service.get_version(version_id, user_id)

    if not version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume version not found",
        )

    return version


# ==================== Metadata Endpoints ====================


@router.get("/resumes/metadata/{metadata_id}", response_model=ResumeMetadataResponse)
async def get_metadata(
    metadata_id: uuid.UUID,
    current_user: UserResponse = Depends(get_current_user),
):
    """Get specific metadata by ID."""
    user_id = uuid.UUID(current_user.id)
    async with UnitOfWorkFactory() as uow:
        service = ResumeService(uow)
        metadata = await service.get_metadata(metadata_id, user_id)

    if not metadata:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Metadata not found",
        )

    return metadata


@router.put("/resumes/metadata/{metadata_id}", response_model=ResumeMetadataResponse)
async def update_metadata(
    metadata_id: uuid.UUID,
    request: ResumeMetadataRequest,
    current_user: UserResponse = Depends(get_current_user),
):
    """Update metadata manually."""
    user_id = uuid.UUID(current_user.id)
    async with UnitOfWorkFactory() as uow:
        service = ResumeService(uow)
        metadata = await service.update_metadata(
            metadata_id, user_id, **request.model_dump(exclude_unset=True)
        )

    if not metadata:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Metadata not found",
        )

    return metadata


@router.post(
    "/resumes/metadata/{metadata_id}/enhance", response_model=ResumeMetadataResponse
)
async def enhance_metadata(
    metadata_id: uuid.UUID,
    request: AIEnhanceRequest,
    current_user: UserResponse = Depends(get_current_user),
):
    """Enhance metadata using AI."""
    user_id = uuid.UUID(current_user.id)
    async with UnitOfWorkFactory() as uow:
        service = ResumeService(uow)
        metadata = await service.enhance_metadata(metadata_id, user_id, request)

    if not metadata:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Metadata not found",
        )

    return metadata


# ==================== Education Endpoints ====================


@router.get(
    "/resumes/educations/{education_id}", response_model=ResumeEducationResponse
)
async def get_education(
    education_id: uuid.UUID,
    current_user: UserResponse = Depends(get_current_user),
):
    """Get specific education entry by ID."""
    user_id = uuid.UUID(current_user.id)
    async with UnitOfWorkFactory() as uow:
        service = ResumeService(uow)
        education = await service.get_education(education_id, user_id)

    if not education:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Education entry not found",
        )

    return education


@router.put(
    "/resumes/educations/{education_id}", response_model=ResumeEducationResponse
)
async def update_education(
    education_id: uuid.UUID,
    request: ResumeEducationRequest,
    current_user: UserResponse = Depends(get_current_user),
):
    """Update education entry manually."""
    user_id = uuid.UUID(current_user.id)
    async with UnitOfWorkFactory() as uow:
        service = ResumeService(uow)
        education = await service.update_education(
            education_id, user_id, **request.model_dump(exclude_unset=True)
        )

    if not education:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Education entry not found",
        )

    return education


@router.post(
    "/resumes/educations/{education_id}/enhance", response_model=ResumeEducationResponse
)
async def enhance_education(
    education_id: uuid.UUID,
    request: AIEnhanceRequest,
    current_user: UserResponse = Depends(get_current_user),
):
    """Enhance education entry using AI."""
    user_id = uuid.UUID(current_user.id)
    async with UnitOfWorkFactory() as uow:
        service = ResumeService(uow)
        education = await service.enhance_education(education_id, user_id, request)

    if not education:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Education entry not found",
        )

    return education


# ==================== Work Experience Endpoints ====================


@router.get(
    "/resumes/work_experiences/{work_id}", response_model=ResumeWorkExperienceResponse
)
async def get_work_experience(
    work_id: uuid.UUID,
    current_user: UserResponse = Depends(get_current_user),
):
    """Get specific work experience by ID."""
    user_id = uuid.UUID(current_user.id)
    async with UnitOfWorkFactory() as uow:
        service = ResumeService(uow)
        work = await service.get_work_experience(work_id, user_id)

    if not work:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Work experience not found",
        )

    return work


@router.put(
    "/resumes/work_experiences/{work_id}", response_model=ResumeWorkExperienceResponse
)
async def update_work_experience(
    work_id: uuid.UUID,
    request: ResumeWorkExperienceRequest,
    current_user: UserResponse = Depends(get_current_user),
):
    """Update work experience manually."""
    user_id = uuid.UUID(current_user.id)
    async with UnitOfWorkFactory() as uow:
        service = ResumeService(uow)
        work = await service.update_work_experience(
            work_id, user_id, **request.model_dump(exclude_unset=True)
        )

    if not work:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Work experience not found",
        )

    return work


@router.post(
    "/resumes/work_experiences/{work_id}/enhance",
    response_model=ResumeWorkExperienceResponse,
)
async def enhance_work_experience(
    work_id: uuid.UUID,
    request: AIEnhanceRequest,
    current_user: UserResponse = Depends(get_current_user),
):
    """Enhance work experience using AI."""
    user_id = uuid.UUID(current_user.id)
    async with UnitOfWorkFactory() as uow:
        service = ResumeService(uow)
        work = await service.enhance_work_experience(work_id, user_id, request)

    if not work:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Work experience not found",
        )

    return work


# ==================== Project Endpoints ====================


@router.get("/resumes/projects/{project_id}", response_model=ResumeProjectResponse)
async def get_project(
    project_id: uuid.UUID,
    current_user: UserResponse = Depends(get_current_user),
):
    """Get specific project by ID."""
    user_id = uuid.UUID(current_user.id)
    async with UnitOfWorkFactory() as uow:
        service = ResumeService(uow)
        project = await service.get_project(project_id, user_id)

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    return project


@router.put("/resumes/projects/{project_id}", response_model=ResumeProjectResponse)
async def update_project(
    project_id: uuid.UUID,
    request: ResumeProjectRequest,
    current_user: UserResponse = Depends(get_current_user),
):
    """Update project manually."""
    user_id = uuid.UUID(current_user.id)
    async with UnitOfWorkFactory() as uow:
        service = ResumeService(uow)
        project = await service.update_project(
            project_id, user_id, **request.model_dump(exclude_unset=True)
        )

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    return project


@router.post(
    "/resumes/projects/{project_id}/enhance", response_model=ResumeProjectResponse
)
async def enhance_project(
    project_id: uuid.UUID,
    request: AIEnhanceRequest,
    current_user: UserResponse = Depends(get_current_user),
):
    """Enhance project using AI."""
    user_id = uuid.UUID(current_user.id)
    async with UnitOfWorkFactory() as uow:
        service = ResumeService(uow)
        project = await service.enhance_project(project_id, user_id, request)

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    return project


# ==================== Skill Endpoints ====================


@router.get("/resumes/skills/{skill_id}", response_model=ResumeSkillResponse)
async def get_skill(
    skill_id: uuid.UUID,
    current_user: UserResponse = Depends(get_current_user),
):
    """Get specific skill by ID."""
    user_id = uuid.UUID(current_user.id)
    async with UnitOfWorkFactory() as uow:
        service = ResumeService(uow)
        skill = await service.get_skill(skill_id, user_id)

    if not skill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Skill not found",
        )

    return skill


@router.put("/resumes/skills/{skill_id}", response_model=ResumeSkillResponse)
async def update_skill(
    skill_id: uuid.UUID,
    request: ResumeSkillRequest,
    current_user: UserResponse = Depends(get_current_user),
):
    """Update skill manually."""
    user_id = uuid.UUID(current_user.id)
    async with UnitOfWorkFactory() as uow:
        service = ResumeService(uow)
        skill = await service.update_skill(
            skill_id, user_id, **request.model_dump(exclude_unset=True)
        )

    if not skill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Skill not found",
        )

    return skill


@router.post("/resumes/skills/{skill_id}/enhance", response_model=ResumeSkillResponse)
async def enhance_skill(
    skill_id: uuid.UUID,
    request: AIEnhanceRequest,
    current_user: UserResponse = Depends(get_current_user),
):
    """Enhance skill using AI."""
    user_id = uuid.UUID(current_user.id)
    async with UnitOfWorkFactory() as uow:
        service = ResumeService(uow)
        skill = await service.enhance_skill(skill_id, user_id, request)

    if not skill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Skill not found",
        )

    return skill
