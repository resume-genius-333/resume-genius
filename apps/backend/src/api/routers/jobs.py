"""Jobs router using service layer architecture."""

import asyncio
import uuid
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from dependency_injector.wiring import inject
from langfuse import observe
from src.api.dependencies import get_current_user
from src.core.unit_of_work import UnitOfWorkFactory
from src.models.api.core import PaginatedResponse
from src.models.api.job import (
    CreateJobRequest,
    CreateJobResponse,
    RefineResumeResponse,
)
from src.models.db.profile.user import ProfileUserSchema
from src.models.db.resumes.job import JobSchema
from src.services.job_service import JobService
from src.services.selection_service import SelectionResult, SelectionService
from src.services.status_service import StatusService, ProcessingStatus
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@observe(name="create job in background")
async def _create_job_background(
    user_id: uuid.UUID, job_id: uuid.UUID, request: CreateJobRequest
):
    """Background task for creating a job."""
    try:
        async with UnitOfWorkFactory() as uow:
            job_service = JobService(uow)
            selection_service = SelectionService(uow)
            job_result = job_service.create_job(
                user_id=user_id,
                job_id=job_id,
                job_description=request.job_description,
                job_url=request.job_url,
            )
            select_education_result = selection_service.select_educations(
                user_id=user_id, job_id=job_id, job_description=request.job_description
            )
            # select_work_experience_result = selection_service.select_work_experience(

            # )
            await asyncio.gather(job_result, select_education_result)
            await uow.commit()
    except Exception as e:
        logger.error(f"Error in background job creation: {str(e)}")
        raise


@router.post("/jobs/create", response_model=CreateJobResponse)
async def create_job(
    request: CreateJobRequest,
    background_tasks: BackgroundTasks,
    current_user: ProfileUserSchema = Depends(get_current_user),
):
    """Create a new job and process it in the background."""
    user_id = current_user.id
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
    current_user: ProfileUserSchema = Depends(get_current_user),
):
    """List all jobs for the current user with pagination."""
    logger.info(f"page_size: {page_size}, page: {page}")
    async with UnitOfWorkFactory() as uow:
        job_service = JobService(uow)
        jobs = await job_service.get_user_jobs(
            user_id=current_user.id, page_size=page_size, page=page
        )
        return jobs


@router.get("/jobs/{job_id}", response_model=JobSchema)
async def get_job(
    job_id: uuid.UUID,
    user: ProfileUserSchema = Depends(get_current_user),
):
    """Get a specific job by ID."""
    async with UnitOfWorkFactory() as uow:
        job_service = JobService(uow)
        job = await job_service.get_job(user_id=user.id, job_id=job_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Job not found"
            )
        return job


# We don't choose this option because this makes the code more coupled with
# implementation detail.
#
# def create_experience_getter(
#     experience_name: str,
#     service_cls: Type,
#     get_get_fn: Callable[[JobService], Callable[[uuid.UUID, uuid.UUID], Any]],
# ):
#     path = r"/jobs/{job_id}" + f"/selected_{experience_name}"

#     @router.get(path)
#     async def getter(
#         job_id: uuid.UUID,
#         current_user: UserResponse = Depends(get_current_user),
#     ):
#         """Select relevant information from user's resume for the job."""
#         async with UnitOfWorkFactory() as uow:
#             service = service_cls(uow)
#             user_id = uuid.UUID(current_user.id)
#             get_fn = get_get_fn(service)
#             # job_id: uuid, user_id: uuid -> result
#             result = await get_fn(job_id, user_id)
#             await uow.commit()
#             return result

#     return getter


# get_selected_educations = create_experience_getter(
#     experience_name="educations",
#     service_cls=JobService,
#     get_get_fn=lambda service: service.get_selected_educations,
# )


@router.get(
    "/jobs/{job_id}/selected_educations",
    response_model=SelectionResult,
)
async def get_job_selected_educations(
    job_id: uuid.UUID,
    current_user: ProfileUserSchema = Depends(get_current_user),
) -> SelectionResult:
    """Select relevant information from user's resume for the job."""
    async with UnitOfWorkFactory() as uow:
        selection_service = SelectionService(uow)
        user_id = current_user.id
        result = await selection_service.get_selected_educations(
            job_id=job_id, user_id=user_id
        )
        await uow.commit()
        if not result:
            raise HTTPException(
                status_code=404, detail="No education selection available."
            )
        return result


@router.get("/jobs/{job_id}/selected_work_experiences")
async def get_job_selected_work_experiences(
    job_id: uuid.UUID,
    current_user: ProfileUserSchema = Depends(get_current_user),
):
    """Select relevant information from user's resume for the job."""
    # async with UnitOfWorkFactory() as uow:
    #     job_service = JobService(uow)
    #     user_id = uuid.UUID(current_user.id)
    #     result = await job_service.get_selected_work_experiences(job_id, user_id)
    #     await uow.commit()
    #     return result


@router.get("/jobs/{job_id}/selected_projects")
async def get_job_selected_projects(
    job_id: uuid.UUID,
    current_user: ProfileUserSchema = Depends(get_current_user),
):
    """Select relevant information from user's resume for the job."""
    # async with UnitOfWorkFactory() as uow:
    #     job_service = JobService(uow)
    #     user_id = uuid.UUID(current_user.id)
    #     result = await job_service.get_selected_projects(job_id, user_id)
    #     await uow.commit()
    #     return result


@router.get("/jobs/{job_id}/selected_skills")
async def get_job_selected_skills(
    job_id: uuid.UUID,
    current_user: ProfileUserSchema = Depends(get_current_user),
):
    """Select relevant information from user's resume for the job."""
    # async with UnitOfWorkFactory() as uow:
    #     job_service = JobService(uow)
    #     user_id = uuid.UUID(current_user.id)
    #     result = await job_service.get_selected_skills(job_id, user_id)
    #     await uow.commit()
    #     return result


@router.post("/jobs/{job_id}/confirm_experience_selection")
async def confirm_job_experience_selection(
    job_id: uuid.UUID,
    current_user: ProfileUserSchema = Depends(get_current_user),
):
    """Select relevant information from user's resume for the job."""
    async with UnitOfWorkFactory() as uow:
        job_service = JobService(uow)
        user_id = current_user.id
        result = await job_service.confirm_experience_selection(job_id, user_id)
        await uow.commit()
        return result


@router.post("/jobs/{job_id}/refine", response_model=RefineResumeResponse)
@inject
async def refine_job_resume(
    job_id: uuid.UUID,
    current_user: ProfileUserSchema = Depends(get_current_user),
) -> RefineResumeResponse:
    """Refine user's resume for the specific job."""
    async with UnitOfWorkFactory() as uow:
        job_service = JobService(uow)
        user_id = current_user.id
        result = await job_service.refine_resume(job_id, user_id)
        await uow.commit()
        return RefineResumeResponse(**result)


@router.get("/jobs/{job_id}/status-stream")
async def stream_job_status(
    job_id: uuid.UUID,
    current_user: ProfileUserSchema = Depends(get_current_user),
):
    """Stream job processing status via Server-Sent Events."""
    user_id = current_user.id
    status_service = StatusService()
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
    current_user: ProfileUserSchema = Depends(get_current_user),
) -> ProcessingStatus:
    """Get current processing status for a job."""
    user_id = current_user.id
    status_service = StatusService()
    return await status_service.get_processing_status(user_id, job_id)
