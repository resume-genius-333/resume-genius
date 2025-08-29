from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, JSON, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column
import uuid

from ..base import Base

if TYPE_CHECKING:
    from ..user import User
    from .job import Job
    from .resume import Resume


class ResumeMetadata(Base):
    __tablename__ = "resume_metadata"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    job_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("jobs.id"), nullable=False)
    parent_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("resume_metadata.id"), nullable=True
    )
    user_name: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    location: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    linkedin_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    github_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    portfolio_website: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    custom_styles: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    __table_args__ = (
        UniqueConstraint('user_id', 'job_id', name='uq_resume_metadata_user_job'),
    )

    # Relationships
    user: Mapped["User"] = relationship(foreign_keys=[user_id])
    job: Mapped["Job"] = relationship(back_populates="resume_metadata")
    parent: Mapped[Optional["ResumeMetadata"]] = relationship(
        remote_side=[id],
        foreign_keys=[parent_id]
    )
    resumes: Mapped[list["Resume"]] = relationship(back_populates="resume_metadata")