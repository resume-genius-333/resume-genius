import asyncio
from datetime import datetime, timezone
import json
from typing import Optional
import uuid
from instructor import AsyncInstructor
from pydantic import BaseModel
import redis.asyncio as redis
from fastapi import APIRouter, BackgroundTasks
from dependency_injector.wiring import inject, Provide
from src.containers import Container
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import async_sessionmaker

from src.models.db.resumes.job import Job
from src.models.llm.resumes.job import JobLLMSchema

router = APIRouter()


class CreateJobRequest(BaseModel):
    job_description: str
    job_url: Optional[str] = None


class CreateJobResponse(BaseModel):
    job_id: uuid.UUID
    sse_url: str


class ProcessingStatus(BaseModel):
    job_parsed_at: Optional[datetime] = None


def _status_key(user_id: uuid.UUID, job_id: uuid.UUID) -> str:
    return f"user:{user_id}:job:{job_id}:status"  # Redis key for latest status


def _status_channel(user_id: uuid.UUID, job_id: uuid.UUID) -> str:
    return f"user:{user_id}:job:{job_id}:status-stream"  # Pub/Sub channel for SSE


@inject
async def _create_job(
    user_id: uuid.UUID,
    job_id: uuid.UUID,
    input_body: CreateJobRequest,
    redis_client: redis.Redis = Provide[Container.redis_client],
    instructor: AsyncInstructor = Provide[Container.async_instructor],
    session_factory: async_sessionmaker = Provide[Container.async_session_factory],
):
    import traceback
    import logging

    logger = logging.getLogger(__name__)
    logger.info(f"Starting job creation for user_id={user_id}, job_id={job_id}")
    # await asyncio.sleep(15)

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
        now = datetime.now(timezone.utc)
        status = ProcessingStatus(job_parsed_at=now)

        # Save latest status into Redis (for GET /status)
        await redis_client.set(_status_key(user_id, job_id), status.model_dump_json())

        channel = _status_channel(user_id, job_id)
        await redis_client.publish(channel, status.model_dump_json())
        logger.info(f"Published status to {channel}: {status.model_dump_json()}")

    except Exception as e:
        logger.error(f"Error in _create_job: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        # Re-raise to ensure background task fails properly
        raise


@router.post("/users/{user_id}/jobs/create", response_model=CreateJobResponse)
async def create_job(
    user_id: uuid.UUID,
    input_body: CreateJobRequest,
    background_tasks: BackgroundTasks,
):
    job_id = uuid.uuid4()
    # Add background task that will handle dependency injection
    background_tasks.add_task(
        _create_job_background_wrapper, user_id, job_id, input_body
    )
    return CreateJobResponse(
        job_id=job_id,
        sse_url=f"http://localhost:8000/api/v1/users/{user_id}/jobs/{job_id}/status",
    )


@inject
async def _create_job_background_wrapper(
    user_id: uuid.UUID,
    job_id: uuid.UUID,
    input_body: CreateJobRequest,
    redis_client: redis.Redis = Provide[Container.redis_client],
    instructor: AsyncInstructor = Provide[Container.async_instructor],
    session_factory: async_sessionmaker = Provide[Container.async_session_factory],
):
    """Wrapper function that handles dependency injection for background task."""
    # Only pass the non-injected parameters, let _create_job's @inject handle the rest
    await _create_job(user_id, job_id, input_body)


@router.post("/users/{user_id}/jobs/{job_id}/select_relevant_info")
async def select_relevant_info(user_id: uuid.UUID, job_id: uuid.UUID):
    pass


@router.post("/users/{user_id}/jobs/{job_id}/refine")
async def refine_resume(
    user_id: uuid.UUID,
    job_id: uuid.UUID,
):
    return {"status": "success", "message": "Resume refinement started"}


@inject
async def _stream_status(
    user_id: uuid.UUID,
    job_id: uuid.UUID,
    redis_client: redis.Redis = Provide[Container.redis_client],
):
    import logging

    logger = logging.getLogger(__name__)
    channel = _status_channel(user_id, job_id)

    logger.info(f"SSE: Starting stream for channel: {channel}")
    logger.info(f"SSE: user_id={user_id}, job_id={job_id}")

    pubsub = redis_client.pubsub()
    await pubsub.subscribe(channel)
    logger.info(f"SSE: Subscribed to Redis channel: {channel}")

    try:
        # Listen for messages
        async for message in pubsub.listen():
            logger.info(
                f"SSE: Received message type: {message['type']}, {json.dumps(message)}"
            )

            if message["type"] == "message":
                logger.info(f"SSE: Message received on channel {channel}")
                print(message["data"])

                data = message["data"]
                if isinstance(data, bytes):
                    data = data.decode("utf-8")
                    logger.debug("SSE: Decoded bytes to string")

                logger.info(f"SSE: Yielding data: {data[:200]}...")
                yield f"data: {data}\n\n"

            elif message["type"] == "subscribe":
                logger.info("SSE: Successfully subscribed to channel")

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
    "/users/{user_id}/jobs/{job_id}/status-stream"
)  # No reponse_model because SSE is a byte stream, not a JSON body
async def stream_status(
    user_id: uuid.UUID,
    job_id: uuid.UUID,
):
    return StreamingResponse(
        _stream_status(user_id, job_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable proxy buffering
        },
    )


@router.get("/users/{user_id}/jobs/{job_id}/status", response_model=ProcessingStatus)
@inject
async def get_status(
    user_id: uuid.UUID,
    job_id: uuid.UUID,
    redis_client: redis.Redis = Provide[Container.redis_client],
):
    raw = await redis_client.get(_status_key(user_id, job_id))  # raw is a JSON string
    if not raw:
        return ProcessingStatus()
    try:
        return ProcessingStatus.model_validate_json(
            raw
        )  # Returns a fully constructed ProcessingStatus instance
    except Exception:
        return ProcessingStatus()