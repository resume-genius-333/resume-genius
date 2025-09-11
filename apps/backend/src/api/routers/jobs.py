from datetime import datetime, timezone
from typing import Literal, Optional
import uuid
from instructor import AsyncInstructor
from pydantic import BaseModel
import redis.asyncio as redis
from fastapi import APIRouter, BackgroundTasks, Depends
from dependency_injector.wiring import inject, Provide
from src.api.dependencies import get_current_user
from src.containers import Container
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import async_sessionmaker

from src.models.auth.user import UserResponse
from src.models.db.resumes.job import Job, JobSchema
from src.models.llm.resumes.job import JobLLMSchema
import logging
import traceback

logger = logging.getLogger(__name__)

router = APIRouter()


class CreateJobRequest(BaseModel):
    job_description: str
    job_url: Optional[str] = None


class CreateJobResponse(BaseModel):
    job_id: uuid.UUID
    sse_url: str


type ProcessingStatusType = Literal["job-parsed-at"]


def _status_key(
    user_id: uuid.UUID, job_id: uuid.UUID, tag: ProcessingStatusType
) -> str:
    return f"user:{user_id}:job:{job_id}:{tag}:status"  # Redis key for latest status


def _status_channel(user_id: uuid.UUID, job_id: uuid.UUID) -> str:
    return f"user:{user_id}:job:{job_id}:status-stream"  # Pub/Sub channel for SSE


class ProcessingStatus(BaseModel):
    job_parsed_at: Optional[datetime] = None


class ProcessingStatusUpdate(BaseModel):
    timestamp: datetime
    tag: ProcessingStatusType


@inject
async def get_processing_status(
    user_id: uuid.UUID,
    job_id: uuid.UUID,
    redis_client: redis.Redis = Provide[Container.redis_client],
) -> ProcessingStatus:
    job_parsed_at = await redis_client.get(
        _status_key(user_id, job_id, "job-parsed-at")
    )
    return ProcessingStatus(job_parsed_at=datetime.fromisoformat(job_parsed_at))


@inject
async def set_and_publish_processing_status(
    user_id: uuid.UUID,
    job_id: uuid.UUID,
    tag: ProcessingStatusType,
    timestamp: Optional[datetime] = None,
    redis_client: redis.Redis = Provide[Container.redis_client],
):
    if not timestamp:
        timestamp = datetime.now(timezone.utc)
    await redis_client.set(_status_key(user_id, job_id, tag), timestamp.isoformat())
    # TODO: Implement publish issues
    update = ProcessingStatusUpdate(timestamp=timestamp, tag=tag)
    await redis_client.publish(
        _status_channel(user_id, job_id), update.model_dump_json()
    )


@inject
async def _create_job(
    user_id: uuid.UUID,
    job_id: uuid.UUID,
    input_body: CreateJobRequest,
    instructor: AsyncInstructor = Provide[Container.async_instructor],
    session_factory: async_sessionmaker = Provide[Container.async_session_factory],
):
    logger.info(f"Starting job creation for user_id={user_id}, job_id={job_id}")
    try:
        # Log LLM call
        logger.info("Calling LLM with job description")
        result = await instructor.create(
            model="gpt-5-nano",
            response_model=JobLLMSchema,
            messages=[
                {
                    "role": "user",
                    "content": f"Extract information from the job description. \n\n{input_body.job_description}",
                }
            ],
        )
        logger.info(f"LLM response received: {result.model_dump_json(indent=2)}")

        # Create job from LLM result
        logger.info("Creating Job object from LLM result")
        job = Job.from_llm(
            user_id=user_id,
            job_id=job_id,
            llm_schema=result,
            job_url=input_body.job_url,
        )

        # Save to database
        logger.info("Saving job to database")
        async with session_factory() as session:
            session.add(job)
            await session.commit()
            logger.info(f"Job saved to database: job_id={job_id}")

        # Compute status
        # now = datetime.now(timezone.utc)
        # status = ProcessingStatus(job_parsed_at=now)

        await set_and_publish_processing_status(user_id, job_id, "job-parsed-at")

        # channel = _status_channel(user_id, job_id)
        # await redis_client.publish(channel, status.model_dump_json())
        # logger.info(f"Published status to {channel}: {status.model_dump_json()}")

    except Exception as e:
        logger.error(f"Error in _create_job: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        # Re-raise to ensure background task fails properly
        raise


@router.post("/jobs/create", response_model=CreateJobResponse)
async def create_job(
    input_body: CreateJobRequest,
    background_tasks: BackgroundTasks,
    current_user: UserResponse = Depends(get_current_user),
):
    user_id = uuid.UUID(current_user.id)
    job_id = uuid.uuid4()
    # Add background task that will handle dependency injection
    background_tasks.add_task(_create_job, user_id, job_id, input_body)
    return CreateJobResponse(
        job_id=job_id,
        sse_url=f"http://localhost:8000/api/v1/users/{user_id}/jobs/{job_id}/status",
    )


@inject
async def _get_job(
    user_id: uuid.UUID,
    job_id: uuid.UUID,
    session_factory: async_sessionmaker = Provide[Container.async_session_factory],
):
    async with session_factory() as session:
        job = await session.get(Job, job_id)
        return job.schema


@router.get("/users/{user_id}/jobs/{job_id}", response_model=JobSchema)
async def get_job(user_id: uuid.UUID, job_id: uuid.UUID):
    return await _get_job(user_id, job_id)


@router.post("/jobs/{job_id}/select_relevant_info")
async def select_relevant_info(
    job_id: uuid.UUID,
    current_user: UserResponse = Depends(get_current_user),
):
    _user_id = uuid.UUID(current_user.id)
    pass


@router.post("/jobs/{job_id}/refine")
async def refine_resume(
    job_id: uuid.UUID,
    current_user: UserResponse = Depends(get_current_user),
):
    return {"status": "success", "message": "Resume refinement started"}


@inject
async def _stream_status(
    user_id: uuid.UUID,
    job_id: uuid.UUID,
    redis_client: redis.Redis = Provide[Container.redis_client],
):
    channel = _status_channel(user_id, job_id)

    pubsub = redis_client.pubsub()
    await pubsub.subscribe(channel)

    try:
        # Listen for messages
        async for message in pubsub.listen():
            if message["type"] == "message":
                data = message["data"]
                info = ProcessingStatusUpdate.model_validate_json(data)
                logger.debug(f"Received update: {info.model_dump_json(indent=2)}")

            elif message["type"] == "subscribe":
                logger.info("SSE: Successfully subscribed to channel")

            result = await get_processing_status(user_id, job_id)
            yield f"data: {result.model_dump_json()}\n\n"

    except Exception as e:
        logger.error(f"SSE: Error in stream: {str(e)}")
        raise

    finally:
        # Clean up
        logger.info(f"SSE: Cleaning up - unsubscribing from {channel}")
        await pubsub.unsubscribe(channel)
        await pubsub.close()
        logger.info(f"SSE: Stream closed for {channel}")


@router.get(
    "/jobs/{job_id}/status-stream"
)  # No reponse_model because SSE is a byte stream, not a JSON body
async def stream_status(
    job_id: uuid.UUID,
    current_user: UserResponse = Depends(get_current_user),
):
    return StreamingResponse(
        _stream_status(uuid.UUID(current_user.id), job_id),
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
):
    return await get_processing_status(uuid.UUID(current_user.id), job_id)
