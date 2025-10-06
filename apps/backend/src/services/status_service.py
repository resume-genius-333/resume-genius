"""Service for managing processing status and SSE streaming."""

from datetime import datetime, timezone
from typing import AsyncGenerator, Optional
import uuid
import redis.asyncio as redis
from pydantic import BaseModel
import logging
from dependency_injector.wiring import Provide, inject
from sqlalchemy.ext.asyncio import async_sessionmaker

from src.containers import Container, container
from src.models.db.status.status import ProcessingStatusTag
from src.repositories.status_repository import StatusRepository

logger = logging.getLogger(__name__)
container.wire(modules=[__name__])


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
    tag: ProcessingStatusTag


class StatusService:
    """Service for managing job processing status and SSE streaming."""

    @inject
    def __init__(
        self,
        redis_client: redis.Redis = Provide[Container.redis_client],
        session_factory: async_sessionmaker = Provide[Container.async_session_factory],
    ):
        """Initialize status service with Redis client."""
        self.redis_client = redis_client
        self._session_factory = session_factory

    def _status_key(
        self, user_id: uuid.UUID, job_id: uuid.UUID, tag: ProcessingStatusTag
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
        async with self._session_factory() as session:
            repository = StatusRepository(session)
            statuses = await repository.get_statuses_for_job(user_id, job_id)

        status_map = {
            status.tag.value: status.recorded_at
            for status in statuses
            if status.recorded_at
        }

        return ProcessingStatus(
            job_parsed_at=status_map.get(ProcessingStatusTag.JOB_PARSED_AT.value),
            educations_selected_at=status_map.get(
                ProcessingStatusTag.EDUCATIONS_SELECTED_AT.value
            ),
            work_experiences_selected_at=status_map.get(
                ProcessingStatusTag.WORK_EXPERIENCES_SELECTED_AT.value
            ),
            projects_selected_at=status_map.get(
                ProcessingStatusTag.PROJECTS_SELECTED_AT.value
            ),
            skills_selected_at=status_map.get(
                ProcessingStatusTag.SKILLS_SELECTED_AT.value
            ),
        )

    async def set_and_publish_status(
        self,
        user_id: uuid.UUID,
        job_id: uuid.UUID,
        tag: ProcessingStatusTag | str,
        timestamp: Optional[datetime] = None,
    ) -> None:
        """Set status in Redis and publish update to subscribers."""
        if not timestamp:
            timestamp = datetime.now(timezone.utc)

        if isinstance(tag, str):
            tag = ProcessingStatusTag(tag)

        async with self._session_factory() as session:
            repository = StatusRepository(session)
            try:
                await repository.upsert_status(
                    user_id=user_id,
                    job_id=job_id,
                    tag=tag,
                    recorded_at=timestamp,
                )
                await session.commit()
            except Exception:
                await session.rollback()
                logger.exception(
                    "Failed to persist status update for user_id=%s job_id=%s tag=%s",
                    user_id,
                    job_id,
                    tag,
                )
                raise

        # Mirror status in Redis for quick lookups and SSE listeners
        await self.redis_client.set(
            self._status_key(user_id, job_id, tag), timestamp.isoformat()
        )

        # Publish update
        update = ProcessingStatusUpdate(timestamp=timestamp, tag=tag)
        await self.redis_client.publish(
            self._status_channel(user_id, job_id), update.model_dump_json()
        )

        logger.info(
            "Published status update: user_id=%s, job_id=%s, tag=%s",
            user_id,
            job_id,
            tag,
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
