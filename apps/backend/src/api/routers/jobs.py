import time
from typing import Optional
import uuid
from instructor import AsyncInstructor
from pydantic import BaseModel
import redis.asyncio as redis
from fastapi import APIRouter, Depends, BackgroundTasks
from dependency_injector.wiring import inject, Provide
from src.containers import Container
from fastapi.responses import StreamingResponse
import json
from sqlalchemy.ext.asyncio import async_sessionmaker

from src.models.db.resumes.job import Job
from src.models.llm.resumes.job import JobLLMSchema


router = APIRouter()


class CreateJobRequest(BaseModel):
    job_description: str
    job_url: Optional[str] = None


class CreateJobResponse(BaseModel):
    job_id: str


@inject
async def _create_job(
    user_id: str,
    job_id: uuid.UUID,
    input_body: CreateJobRequest,
    redis_client: redis.Redis = Provide[Container.redis_client],
    instructor: AsyncInstructor = Provide[Container.async_instructor],
    session_factory: async_sessionmaker = Provide[Container.async_session_factory],
):
    # time.sleep(60)
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

    # job = Job(
    #     id=job_id,
    #     user_id=user_id,
    #     company_name=result.company_name,
    #     position_title=result.position_title,
    #     job_description=result.job_description,
    #     job_url=data.job_url,
    # )

    job = Job.from_llm(
        user_id=user_id, job_id=job_id, llm_schema=result, job_url=input_body.job_url
    )

    async with session_factory() as session:
        session.add(job)
        await session.commit()
    await redis_client.publish(
        f"user:{user_id}:job:{job_id}", job.schema.model_dump_json()
    )


@router.post("/users/{user_id}/jobs/create", response_model=CreateJobResponse)
async def create_job(
    user_id: str,
    input_body: CreateJobRequest,
    background_tasks: BackgroundTasks,
    # redis_client: redis.Redis = Depends(Provide[Container.redis_client]),
):
    job_id = uuid.uuid4()
    background_tasks.add_task(_create_job, user_id, job_id, input_body)
    return CreateJobResponse(job_id=job_id.hex)


@router.post("/users/{user_id}/jobs/{job_id}/select_relevant_info")
async def select_relevant_info(user_id: str, job_id: str):
    pass


@router.post("/users/{user_id}/jobs/{job_id}/refine")
@inject
async def refine_resume(
    user_id: str,
    job_id: str,
    redis_client: redis.Redis = Depends(Provide[Container.redis_client]),
):
    await redis_client.publish(
        f"user:{user_id}:job:{job_id}",
        json.dumps({"user_id": user_id, "job_id": job_id}),
    )
    return {"status": "success", "message": "Resume refinement started"}


async def _stream_status(user_id: str, job_id: str, redis_client: redis.Redis):
    pubsub = redis_client.pubsub()
    await pubsub.subscribe(f"user:{user_id}:job:{job_id}")
    try:
        # Listen for messages
        async for message in pubsub.listen():
            if message["type"] == "message":
                yield message["data"]
    finally:
        # Clean up
        await pubsub.unsubscribe(f"user:{user_id}:job:{job_id}")
        await pubsub.close()


@router.get("/users/{user_id}/jobs/{job_id}/status")
@inject
async def stream_status(
    user_id: str,
    job_id: str,
    redis_client: redis.Redis = Depends(Provide[Container.redis_client]),
):
    return StreamingResponse(
        _stream_status(user_id, job_id, redis_client),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable proxy buffering
        },
    )
