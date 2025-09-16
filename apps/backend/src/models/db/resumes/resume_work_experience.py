from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column
import uuid

from ..base import Base

if TYPE_CHECKING:
    from ..user import User
    from .job import Job


from pydantic import BaseModel, PrivateAttr


class ResumeWorkExperienceSchema(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    job_id: uuid.UUID
    parent_id: uuid.UUID | None = None
    job_title: str
    company_name: str
    employment_type: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    location: str | None = None
    _orm_entity: Optional["ResumeWorkExperience"] = PrivateAttr(default=None)

    class Config:
        from_attributes = True


class ResumeWorkExperience(Base):
    __tablename__ = "resume_work_experiences"

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
        UUID(as_uuid=True), ForeignKey("resume_work_experiences.id"), nullable=True
    )
    job_title: Mapped[str] = mapped_column(String, nullable=False)
    company_name: Mapped[str] = mapped_column(String, nullable=False)
    employment_type: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    start_date: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    end_date: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    location: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    __table_args__ = (
        UniqueConstraint(
            "user_id", "job_id", name="uq_resume_work_experience_user_job"
        ),
    )

    # Relationships
    user: Mapped["User"] = relationship(foreign_keys=[user_id])
    job: Mapped["Job"] = relationship(back_populates="resume_work_experiences")
    parent: Mapped[Optional["ResumeWorkExperience"]] = relationship(
        remote_side=[id], foreign_keys=[parent_id]
    )

    @property
    def schema(self):
        result = ResumeWorkExperienceSchema.model_validate(self)
        result._orm_entity = self
        return result
