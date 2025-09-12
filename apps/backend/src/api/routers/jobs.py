"""Jobs router using service layer architecture."""

import uuid
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from dependency_injector.wiring import inject, Provide
from src.api.dependencies import get_current_user
from src.containers import Container
from src.core.unit_of_work import UnitOfWorkFactory
from src.models.api.core import PaginatedResponse
from src.models.auth.user import UserResponse
from src.models.api.job import (
    CreateJobRequest,
    CreateJobResponse,
    RefineResumeResponse,
)
from src.models.db.resumes.job import JobSchema
from src.services.job_service import JobService
from src.services.status_service import StatusService, ProcessingStatus
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@inject
def get_status_service(
    status_service: StatusService = Provide[Container.status_service],
) -> StatusService:
    """Get status service."""
    return status_service


@inject
async def _create_job_background(
    user_id: uuid.UUID, job_id: uuid.UUID, request: CreateJobRequest
):
    """Background task for creating a job."""
    try:
        async with UnitOfWorkFactory() as uow:
            job_service = JobService(uow)
            await job_service.create_job(
                user_id=user_id,
                job_id=job_id,
                job_description=request.job_description,
                job_url=request.job_url,
            )
            await uow.commit()
    except Exception as e:
        logger.error(f"Error in background job creation: {str(e)}")
        raise


@router.post("/jobs/create", response_model=CreateJobResponse)
async def create_job(
    request: CreateJobRequest,
    background_tasks: BackgroundTasks,
    current_user: UserResponse = Depends(get_current_user),
):
    """Create a new job and process it in the background."""
    user_id = uuid.UUID(current_user.id)
    job_id = uuid.uuid4()

    # Add background task with dependency injection
    background_tasks.add_task(
        _create_job_background,
        user_id,
        job_id,
        request,
    )

    return CreateJobResponse(
        job_id=job_id,
        sse_url=f"http://localhost:8000/api/v1/jobs/{job_id}/status-stream",
    )


@router.get("/jobs", response_model=PaginatedResponse[JobSchema])
async def list_jobs(
    page_size: int = 20,
    page: int = 0,
    current_user: UserResponse = Depends(get_current_user),
):
    """List all jobs for the current user with pagination."""
    logger.info(f"page_size: {page_size}, page: {page}")
    async with UnitOfWorkFactory() as uow:
        job_service = JobService(uow)
        jobs = await job_service.get_user_jobs(
            user_id=uuid.UUID(current_user.id), page_size=page_size, page=page
        )
        return jobs


@router.get("/jobs/{job_id}", response_model=JobSchema)
async def get_job(
    job_id: uuid.UUID,
    user: UserResponse = Depends(get_current_user),
):
    """Get a specific job by ID."""
    async with UnitOfWorkFactory() as uow:
        job_service = JobService(uow)
        job = await job_service.get_job(job_id, uuid.UUID(user.id))
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Job not found"
            )
        return job


@router.post("/jobs/{job_id}/select_relevant_info")
@inject
async def select_relevant_info(
    job_id: uuid.UUID,
    current_user: UserResponse = Depends(get_current_user),
):
    """Select relevant information from user's resume for the job."""
    async with UnitOfWorkFactory() as uow:
        job_service = JobService(uow)
        user_id = uuid.UUID(current_user.id)
        result = await job_service.select_relevant_info(job_id, user_id)
        await uow.commit()
        return result


@router.post("/jobs/{job_id}/refine", response_model=RefineResumeResponse)
@inject
async def refine_resume(
    job_id: uuid.UUID,
    current_user: UserResponse = Depends(get_current_user),
) -> RefineResumeResponse:
    """Refine user's resume for the specific job."""
    async with UnitOfWorkFactory() as uow:
        job_service = JobService(uow)
        user_id = uuid.UUID(current_user.id)
        result = await job_service.refine_resume(job_id, user_id)
        await uow.commit()
        return RefineResumeResponse(**result)


@router.get("/jobs/{job_id}/status-stream")
async def stream_status(
    job_id: uuid.UUID,
    current_user: UserResponse = Depends(get_current_user),
):
    """Stream job processing status via Server-Sent Events."""
    user_id = uuid.UUID(current_user.id)
    status_service = get_status_service()
    return StreamingResponse(
        status_service.stream_status(user_id, job_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable proxy buffering
        },
    )


@router.get("/jobs/{job_id}/status", response_model=ProcessingStatus)
async def get_status(
    job_id: uuid.UUID,
    current_user: UserResponse = Depends(get_current_user),
) -> ProcessingStatus:
    """Get current processing status for a job."""
    user_id = uuid.UUID(current_user.id)
    status_service = get_status_service()
    return await status_service.get_processing_status(user_id, job_id)
