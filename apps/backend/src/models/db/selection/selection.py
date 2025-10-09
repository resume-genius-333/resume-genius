"""Database models backing LLM-generated selection results."""

from __future__ import annotations

import datetime
import enum
import uuid
from typing import List

from pydantic import BaseModel
from sqlalchemy import (
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Integer,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.db.base import Base


class SelectionTarget(enum.Enum):
    """Targets that can be selected for a job."""

    EDUCATIONS = "educations"
    WORK_EXPERIENCES = "work_experiences"
    PROJECTS = "projects"
    SKILLS = "skills"


class SelectionItemType(enum.Enum):
    """Flag indicating whether an item was included or excluded."""

    SELECTED = "selected"
    NOT_SELECTED = "not_selected"


class SelectionResultItemSchema(BaseModel):
    """Pydantic representation of a selection item row."""

    id: uuid.UUID
    selection_result_id: uuid.UUID
    profile_item_id: uuid.UUID
    justification: str
    item_type: SelectionItemType
    position: int
    created_at: datetime.datetime
    updated_at: datetime.datetime

    class Config:
        from_attributes = True


class SelectionResultRecordSchema(BaseModel):
    """Pydantic representation of a persisted selection result."""

    id: uuid.UUID
    user_id: uuid.UUID
    job_id: uuid.UUID
    target: SelectionTarget
    created_at: datetime.datetime
    updated_at: datetime.datetime
    items: List[SelectionResultItemSchema]

    class Config:
        from_attributes = True


class SelectionResult(Base):
    """Selection results linked to a job/user pair."""

    __tablename__ = "selection_results"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "job_id",
            "target",
            name="uq_selection_results_user_job_target",
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
    target: Mapped[SelectionTarget] = mapped_column(
        SAEnum(SelectionTarget, name="selection_target"), nullable=False
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

    items: Mapped[List["SelectionResultItem"]] = relationship(
        "SelectionResultItem",
        back_populates="selection_result",
        cascade="all, delete-orphan",
        order_by="SelectionResultItem.position",
    )

    @property
    def schema(self) -> SelectionResultRecordSchema:
        """Return a Pydantic schema containing child items."""

        return SelectionResultRecordSchema(
            id=self.id,
            user_id=self.user_id,
            job_id=self.job_id,
            target=self.target,
            created_at=self.created_at,
            updated_at=self.updated_at,
            items=[item.schema for item in self.items],
        )


class SelectionResultItem(Base):
    """Individual selected or rejected items for a selection result."""

    __tablename__ = "selection_result_items"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    selection_result_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("selection_results.id", ondelete="CASCADE"),
        nullable=False,
    )
    profile_item_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    justification: Mapped[str] = mapped_column(Text, nullable=False)
    item_type: Mapped[SelectionItemType] = mapped_column(
        SAEnum(SelectionItemType, name="selection_item_type"), nullable=False
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    selection_result: Mapped[SelectionResult] = relationship(
        "SelectionResult",
        back_populates="items",
    )

    @property
    def schema(self) -> SelectionResultItemSchema:
        return SelectionResultItemSchema.model_validate(self, from_attributes=True)
