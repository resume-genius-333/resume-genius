"""Repository for persisted job processing statuses."""

from __future__ import annotations

import datetime
import uuid
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.db.status.status import (
    ProcessingStatusTag,
    Status,
    StatusRecordSchema,
)


class StatusRepository:
    """Encapsulates database access for job processing statuses."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_statuses_for_job(
        self,
        user_id: uuid.UUID,
        job_id: uuid.UUID,
    ) -> List[StatusRecordSchema]:
        """Fetch all status records for a given user/job pair."""
        stmt = (
            select(Status)
            .where(Status.user_id == user_id)
            .where(Status.job_id == job_id)
        )
        result = await self.session.execute(stmt)
        statuses = list(result.scalars().all())
        return [status.schema for status in statuses]

    async def get_status(
        self,
        user_id: uuid.UUID,
        job_id: uuid.UUID,
        tag: ProcessingStatusTag,
    ) -> Optional[StatusRecordSchema]:
        """Return a single status record if it exists."""
        stmt = (
            select(Status)
            .where(Status.user_id == user_id)
            .where(Status.job_id == job_id)
            .where(Status.tag == tag)
        )
        result = await self.session.execute(stmt)
        status = result.scalar_one_or_none()
        return status.schema if status else None

    async def upsert_status(
        self,
        user_id: uuid.UUID,
        job_id: uuid.UUID,
        tag: ProcessingStatusTag,
        recorded_at: datetime.datetime,
    ) -> StatusRecordSchema:
        """Create or update a status timestamp for the supplied tag."""
        stmt = (
            select(Status)
            .where(Status.user_id == user_id)
            .where(Status.job_id == job_id)
            .where(Status.tag == tag)
            .with_for_update()
        )
        result = await self.session.execute(stmt)
        status = result.scalar_one_or_none()

        if status is None:
            status = Status(
                user_id=user_id,
                job_id=job_id,
                tag=tag,
                recorded_at=recorded_at,
            )
            self.session.add(status)
        else:
            status.recorded_at = recorded_at

        await self.session.flush()
        await self.session.refresh(status)
        return status.schema
