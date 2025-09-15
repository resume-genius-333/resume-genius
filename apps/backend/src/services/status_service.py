"""Service for managing processing status and SSE streaming."""

import asyncio
from datetime import datetime, timezone
from typing import AsyncGenerator, Literal, Optional
import uuid
import redis.asyncio as redis
from pydantic import BaseModel
import logging
from dependency_injector.wiring import Provide, inject
from src.containers import Container, container

logger = logging.getLogger(__name__)
container.wire(modules=[__name__])


type ProcessingStatusType = Literal[
    "job-parsed-at",
    "educations-selected-at",
    "work-experiences-selected-at",
    "projects-selected-at",
    "skills-selected-at",
]


class ProcessingStatus(BaseModel):
    """Processing status model."""

    job_parsed_at: Optional[datetime] = None
    educations_selected_at: Optional[datetime] = None
    work_experiences_selected_at: Optional[datetime] = None
    projects_selected_at: Optional[datetime] = None
    skills_selected_at: Optional[datetime] = None


class ProcessingStatusUpdate(BaseModel):
    """Status update for SSE streaming."""

    timestamp: datetime
    tag: ProcessingStatusType


class StatusService:
    """Service for managing job processing status and SSE streaming."""

    @inject
    def __init__(self, redis_client: redis.Redis = Provide[Container.redis_client]):
        """Initialize status service with Redis client."""
        self.redis_client = redis_client

    def _status_key(
        self, user_id: uuid.UUID, job_id: uuid.UUID, tag: ProcessingStatusType
    ) -> str:
        """Generate Redis key for status storage."""
        return f"user:{user_id}:job:{job_id}:{tag}:status"

    def _status_channel(self, user_id: uuid.UUID, job_id: uuid.UUID) -> str:
        """Generate Redis pub/sub channel for SSE streaming."""
        return f"user:{user_id}:job:{job_id}:status-stream"

    async def get_processing_status(
        self, user_id: uuid.UUID, job_id: uuid.UUID
    ) -> ProcessingStatus:
        """Get current processing status for a job."""

        def convert(date: Optional[str]) -> Optional[datetime]:
            if not date:
                return None
            return datetime.fromisoformat(date)

        job_parsed_at = self.redis_client.get(
            self._status_key(user_id, job_id, "job-parsed-at")
        )
        educations_selected_at = self.redis_client.get(
            self._status_key(user_id, job_id, "educations-selected-at")
        )
        work_experiences_selected_at = self.redis_client.get(
            self._status_key(user_id, job_id, "work-experiences-selected-at")
        )
        projects_selected_at = self.redis_client.get(
            self._status_key(user_id, job_id, "projects-selected-at")
        )
        skills_selected_at = self.redis_client.get(
            self._status_key(user_id, job_id, "skills-selected-at")
        )
        (
            job_parsed_at,
            educations_selected_at,
            work_experiences_selected_at,
            projects_selected_at,
            skills_selected_at,
        ) = await asyncio.gather(
            job_parsed_at,
            educations_selected_at,
            work_experiences_selected_at,
            projects_selected_at,
            skills_selected_at,
        )

        return ProcessingStatus(
            job_parsed_at=convert(job_parsed_at),
            educations_selected_at=convert(educations_selected_at),
            work_experiences_selected_at=convert(work_experiences_selected_at),
            projects_selected_at=convert(projects_selected_at),
            skills_selected_at=convert(skills_selected_at),
        )

    async def set_and_publish_status(
        self,
        user_id: uuid.UUID,
        job_id: uuid.UUID,
        tag: ProcessingStatusType,
        timestamp: Optional[datetime] = None,
    ) -> None:
        """Set status in Redis and publish update to subscribers."""
        if not timestamp:
            timestamp = datetime.now(timezone.utc)

        # Store status
        await self.redis_client.set(
            self._status_key(user_id, job_id, tag), timestamp.isoformat()
        )

        # Publish update
        update = ProcessingStatusUpdate(timestamp=timestamp, tag=tag)
        await self.redis_client.publish(
            self._status_channel(user_id, job_id), update.model_dump_json()
        )

        logger.info(
            f"Published status update: user_id={user_id}, job_id={job_id}, tag={tag}"
        )

    async def stream_status(
        self, user_id: uuid.UUID, job_id: uuid.UUID
    ) -> AsyncGenerator[str, None]:
        """Stream status updates via Server-Sent Events."""
        channel = self._status_channel(user_id, job_id)
        pubsub = self.redis_client.pubsub()

        await pubsub.subscribe(channel)
        logger.info(f"SSE: Subscribed to channel {channel}")

        try:
            # Send initial status
            initial_status = await self.get_processing_status(user_id, job_id)
            yield f"data: {initial_status.model_dump_json()}\n\n"

            # Listen for updates
            async for message in pubsub.listen():
                if message["type"] == "message":
                    data = message["data"]
                    info = ProcessingStatusUpdate.model_validate_json(data)
                    logger.info(f"Received update: {info.model_dump_json(indent=2)}")

                    # Send current status after update
                    result = await self.get_processing_status(user_id, job_id)
                    yield f"data: {result.model_dump_json()}\n\n"

                elif message["type"] == "subscribe":
                    logger.info("SSE: Successfully subscribed to channel")

                elif message["type"] == "unsubscribe":
                    logger.info("SSE: Successfully unsubscribed from channel")
                    break

        except Exception as e:
            logger.error(f"SSE: Error in stream: {str(e)}")
            raise

        finally:
            # Clean up
            logger.info(f"SSE: Cleaning up - unsubscribing from {channel}")
            await pubsub.unsubscribe(channel)
            await pubsub.close()
            logger.info(f"SSE: Stream closed for {channel}")
