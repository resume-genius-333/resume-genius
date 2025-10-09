"""Service for managing processing status and SSE streaming."""

import asyncio
import logging
import uuid
from datetime import datetime, timezone
from typing import AsyncGenerator, Optional

import redis.asyncio as redis
from dependency_injector.wiring import Provide, inject
from pydantic import BaseModel

from src.containers import Container, container
from src.config.settings import StatusStreamBackend
from src.core.queue_manager import QueueService
from src.core.unit_of_work import UnitOfWork, UnitOfWorkFactory
from src.models.db.status.status import ProcessingStatusTag

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
        redis_client: Optional[redis.Redis] = Provide[Container.redis_client],
        queue_service: QueueService = Provide[Container.queue_service],
        backend_preference: str = Provide[Container.config.status_stream.backend],
    ):
        self.redis_client = redis_client
        self._queue_service = queue_service

        try:
            if isinstance(backend_preference, StatusStreamBackend):
                self._backend_preference = backend_preference
            else:
                self._backend_preference = StatusStreamBackend(backend_preference)
        except ValueError:
            logger.warning(
                "Unknown status stream backend preference '%s'; defaulting to auto",
                backend_preference,
            )
            self._backend_preference = StatusStreamBackend.AUTO

        self._active_backend: StatusStreamBackend | None = None
        self._backend_lock = asyncio.Lock()
        self._redis_health_checked = False
        self._redis_available = False

    async def _ensure_stream_backend(self) -> StatusStreamBackend:
        if self._active_backend is not None:
            return self._active_backend

        async with self._backend_lock:
            if self._active_backend is not None:
                return self._active_backend

            if self._backend_preference == StatusStreamBackend.QUEUE:
                logger.info(
                    "Status streaming backend forced to in-memory queue manager by configuration."
                )
                self._active_backend = StatusStreamBackend.QUEUE
                return self._active_backend

            redis_available = await self._try_enable_redis()

            if self._backend_preference == StatusStreamBackend.REDIS:
                if redis_available:
                    logger.info(
                        "Status streaming backend set to Redis pub/sub as requested."
                    )
                    self._active_backend = StatusStreamBackend.REDIS
                    return self._active_backend

                logger.warning(
                    "Redis backend requested but unavailable; falling back to in-memory queue manager."
                )
                self._active_backend = StatusStreamBackend.QUEUE
                return self._active_backend

            # AUTO selection
            if redis_available:
                logger.info("Status streaming backend auto-selected Redis pub/sub.")
                self._active_backend = StatusStreamBackend.REDIS
            else:
                logger.info(
                    "Status streaming backend auto-selected in-memory queue manager (Redis unavailable)."
                )
                self._active_backend = StatusStreamBackend.QUEUE

            return self._active_backend

    async def _try_enable_redis(self) -> bool:
        if self.redis_client is None:
            logger.info(
                "Redis client not configured; queue manager will be used for status streaming."
            )
            self._redis_health_checked = True
            self._redis_available = False
            return False

        if self._redis_health_checked:
            return self._redis_available

        try:
            await self.redis_client.ping()
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "Redis health check failed; status streaming will use queue manager.",
                exc_info=exc,
            )
            self._redis_available = False
        else:
            logger.info("Redis health check succeeded for status streaming backend.")
            self._redis_available = True
        finally:
            self._redis_health_checked = True

        return self._redis_available

    async def _downgrade_to_queue(
        self, reason: str, exc: Optional[Exception] = None
    ) -> None:
        async with self._backend_lock:
            self._active_backend = StatusStreamBackend.QUEUE
            self._redis_available = False
            self._redis_health_checked = True

        if exc is not None:
            logger.warning(
                "%s; falling back to in-memory queue manager.",
                reason,
                exc_info=exc,
            )
        else:
            logger.warning(
                "%s; falling back to in-memory queue manager.",
                reason,
            )

    def _status_key(
        self, user_id: uuid.UUID, job_id: uuid.UUID, tag: ProcessingStatusTag
    ) -> str:
        """Generate key for caching status snapshots in Redis."""
        return f"user:{user_id}:job:{job_id}:{tag}:status"

    def _status_channel(self, user_id: uuid.UUID, job_id: uuid.UUID) -> str:
        """Generate logical channel identifier for status streaming."""
        return f"user:{user_id}:job:{job_id}:status-stream"

    async def get_processing_status(
        self,
        user_id: uuid.UUID,
        job_id: uuid.UUID,
        uow: UnitOfWork | None = None,
    ) -> ProcessingStatus:
        """Get current processing status for a job."""
        if uow:
            statuses = await uow.status_repository.get_statuses_for_job(user_id, job_id)
        else:
            async with UnitOfWorkFactory() as uow:
                statuses = await uow.status_repository.get_statuses_for_job(
                    user_id, job_id
                )

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
        uow: UnitOfWork | None = None,
    ) -> None:
        """Persist a status update and publish it to the active streaming backend."""
        if not timestamp:
            timestamp = datetime.now(timezone.utc)

        if isinstance(tag, str):
            tag = ProcessingStatusTag(tag)

        if uow:
            await uow.status_repository.upsert_status(
                user_id=user_id,
                job_id=job_id,
                tag=tag,
                recorded_at=timestamp,
            )
        else:
            async with UnitOfWorkFactory() as uow:
                try:
                    await uow.status_repository.upsert_status(
                        user_id=user_id,
                        job_id=job_id,
                        tag=tag,
                        recorded_at=timestamp,
                    )
                    await uow.commit()
                except Exception:
                    await uow.rollback()
                    logger.exception(
                        "Failed to persist status update for user_id=%s job_id=%s tag=%s",
                        user_id,
                        job_id,
                        tag,
                    )
                    raise

        update = ProcessingStatusUpdate(timestamp=timestamp, tag=tag)
        payload = update.model_dump_json()
        channel = self._status_channel(user_id, job_id)

        backend = await self._ensure_stream_backend()

        if backend == StatusStreamBackend.REDIS and self.redis_client is not None:
            try:
                await self.redis_client.set(
                    self._status_key(user_id, job_id, tag), timestamp.isoformat()
                )
                await self.redis_client.publish(channel, payload)
                logger.info(
                    "Published status update via Redis: user_id=%s, job_id=%s, tag=%s",
                    user_id,
                    job_id,
                    tag,
                )
                return
            except Exception as exc:  # noqa: BLE001
                await self._downgrade_to_queue(
                    "Redis publish failed for status update",
                    exc,
                )
                backend = StatusStreamBackend.QUEUE

        if backend == StatusStreamBackend.QUEUE:
            await self._queue_service.notify(channel, payload)
            logger.info(
                "Published status update via queue manager: user_id=%s, job_id=%s, tag=%s",
                user_id,
                job_id,
                tag,
            )
        else:
            logger.error(
                "Status update not published: no active backend for user_id=%s job_id=%s tag=%s",
                user_id,
                job_id,
                tag,
            )

    async def stream_status(
        self, user_id: uuid.UUID, job_id: uuid.UUID
    ) -> AsyncGenerator[str, None]:
        """Stream status updates via Server-Sent Events."""
        channel = self._status_channel(user_id, job_id)
        backend = await self._ensure_stream_backend()

        if backend == StatusStreamBackend.REDIS and self.redis_client is not None:
            pubsub = self.redis_client.pubsub()
            await pubsub.subscribe(channel)
            logger.info("SSE: Subscribed to Redis channel %s", channel)

            try:
                initial_status = await self.get_processing_status(user_id, job_id)
                yield f"data: {initial_status.model_dump_json()}\n\n"

                async for message in pubsub.listen():
                    if message["type"] == "message":
                        data = message["data"]
                        info = ProcessingStatusUpdate.model_validate_json(data)
                        logger.info(
                            "Redis SSE update received: user_id=%s job_id=%s tag=%s",
                            user_id,
                            job_id,
                            info.tag,
                        )
                        result = await self.get_processing_status(user_id, job_id)
                        yield f"data: {result.model_dump_json()}\n\n"
                    elif message["type"] == "unsubscribe":
                        logger.info("SSE: Redis unsubscribe signal for %s", channel)
                        break
            except Exception as exc:  # noqa: BLE001
                logger.error("SSE: Error in Redis stream for %s: %s", channel, exc)
                raise
            finally:
                logger.info("SSE: Cleaning up Redis pubsub for %s", channel)
                await pubsub.unsubscribe(channel)
                await pubsub.close()
                logger.info("SSE: Redis stream closed for %s", channel)
            return

        context = self._queue_service.create_listening_context(channel)
        logger.info("SSE: Subscribed to in-memory queue channel %s", channel)

        async with context as queue:
            try:
                initial_status = await self.get_processing_status(user_id, job_id)
                yield f"data: {initial_status.model_dump_json()}\n\n"

                while True:
                    data = await queue.get()
                    info = ProcessingStatusUpdate.model_validate_json(data)
                    logger.info(
                        "Queue SSE update received: user_id=%s job_id=%s tag=%s",
                        user_id,
                        job_id,
                        info.tag,
                    )
                    result = await self.get_processing_status(user_id, job_id)
                    yield f"data: {result.model_dump_json()}\n\n"
            except asyncio.CancelledError:
                logger.info("SSE: Queue stream cancelled for %s", channel)
                raise
            except Exception as exc:  # noqa: BLE001
                logger.error("SSE: Error in queue stream for %s: %s", channel, exc)
                raise
            finally:
                logger.info("SSE: Queue stream closed for %s", channel)
