from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, ForeignKey, Enum, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column
import uuid

from ..base import Base
from ..enums import EmploymentType

if TYPE_CHECKING:
    from ..user import User
    from .job import Job


class ResumeWorkExperience(Base):
    __tablename__ = "resume_work_experiences"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    job_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("jobs.id"), nullable=False)
    parent_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("resume_work_experiences.id"), nullable=True
    )
    job_title: Mapped[str] = mapped_column(String, nullable=False)
    company_name: Mapped[str] = mapped_column(String, nullable=False)
    employment_type: Mapped[Optional[EmploymentType]] = mapped_column(Enum(EmploymentType), nullable=True)
    start_date: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    end_date: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    location: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    __table_args__ = (
        UniqueConstraint('user_id', 'job_id', name='uq_resume_work_experience_user_job'),
    )

    # Relationships
    user: Mapped["User"] = relationship(foreign_keys=[user_id])
    job: Mapped["Job"] = relationship(back_populates="resume_work_experiences")
    parent: Mapped[Optional["ResumeWorkExperience"]] = relationship(
        remote_side=[id],
        foreign_keys=[parent_id]
    )