"""Database model for tracking job processing status timestamps."""

from __future__ import annotations

import datetime
import enum
import uuid
from typing import Optional

from pydantic import BaseModel, PrivateAttr
from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.models.db.base import Base


class ProcessingStatusTag(enum.Enum):
    """Supported processing stages for a job."""

    JOB_PARSED_AT = "job-parsed-at"
    EDUCATIONS_SELECTED_AT = "educations-selected-at"
    WORK_EXPERIENCES_SELECTED_AT = "work-experiences-selected-at"
    PROJECTS_SELECTED_AT = "projects-selected-at"
    SKILLS_SELECTED_AT = "skills-selected-at"


class StatusRecordSchema(BaseModel):
    """Pydantic schema representing a persisted status record."""

    id: uuid.UUID
    user_id: uuid.UUID
    job_id: uuid.UUID
    tag: ProcessingStatusTag
    recorded_at: datetime.datetime
    created_at: datetime.datetime
    updated_at: datetime.datetime

    _orm_entity: Optional["Status"] = PrivateAttr(default=None)

    class Config:
        from_attributes = True


class Status(Base):
    """Persisted status timestamp for a specific job/user pair."""

    __tablename__ = "job_processing_statuses"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "job_id",
            "tag",
            name="uq_job_processing_statuses_user_job_tag",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("jobs.id"), nullable=False
    )
    tag: Mapped[ProcessingStatusTag] = mapped_column(
        SAEnum(ProcessingStatusTag, name="processing_status_tag"), nullable=False
    )
    recorded_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    @property
    def schema(self) -> StatusRecordSchema:
        """Return the Pydantic representation of the status record."""

        result = StatusRecordSchema.model_validate(self)
        result._orm_entity = self
        return result
