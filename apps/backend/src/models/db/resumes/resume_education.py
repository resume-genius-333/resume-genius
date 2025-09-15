from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Float, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column
import uuid

from ..base import Base

if TYPE_CHECKING:
    from ..user import User
    from .job import Job


from pydantic import BaseModel, PrivateAttr


class ResumeEducationSchema(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    job_id: uuid.UUID
    parent_id: uuid.UUID | None = None
    institution_name: str
    degree: str
    field_of_study: str
    focus_area: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    gpa: float | None = None
    max_gpa: float | None = None
    city: str | None = None
    country: str | None = None
    _orm_entity: Optional["ResumeEducation"] = PrivateAttr(default=None)

    class Config:
        from_attributes = True


class ResumeEducation(Base):
    __tablename__ = "resume_educations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("jobs.id"), nullable=False
    )
    parent_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("resume_educations.id"), nullable=True
    )
    institution_name: Mapped[str] = mapped_column(String, nullable=False)
    degree: Mapped[str] = mapped_column(String, nullable=False)
    field_of_study: Mapped[str] = mapped_column(String, nullable=False)
    focus_area: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    start_date: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    end_date: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    gpa: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    max_gpa: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    country: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    __table_args__ = (
        UniqueConstraint("user_id", "job_id", name="uq_resume_education_user_job"),
    )

    # Relationships
    user: Mapped["User"] = relationship(foreign_keys=[user_id])
    job: Mapped["Job"] = relationship(back_populates="resume_educations")
    parent: Mapped[Optional["ResumeEducation"]] = relationship(
        remote_side=[id], foreign_keys=[parent_id]
    )

    @property
    def schema(self):
        result = ResumeEducationSchema.model_validate(self)
        result._orm_entity = self
        return result
