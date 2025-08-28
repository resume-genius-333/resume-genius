from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship, Mapped, mapped_column
import uuid

from ..base import Base

if TYPE_CHECKING:
    from ..user import User
    from .job import Job
    from .resume_metadata import ResumeMetadata


class Resume(Base):
    __tablename__ = "resumes"

    version: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)
    job_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("jobs.id"), primary_key=True)
    parent_version: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    metadata_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("resume_metadata.id"), nullable=False
    )
    pinned_education_ids: Mapped[List[uuid.UUID]] = mapped_column(ARRAY(UUID(as_uuid=True)), nullable=False, default=[])
    pinned_experience_ids: Mapped[List[uuid.UUID]] = mapped_column(ARRAY(UUID(as_uuid=True)), nullable=False, default=[])
    pinned_project_ids: Mapped[List[uuid.UUID]] = mapped_column(ARRAY(UUID(as_uuid=True)), nullable=False, default=[])
    pinned_skill_ids: Mapped[List[uuid.UUID]] = mapped_column(ARRAY(UUID(as_uuid=True)), nullable=False, default=[])

    # Relationships
    user: Mapped["User"] = relationship(foreign_keys=[user_id])
    job: Mapped["Job"] = relationship(back_populates="resumes")
    metadata: Mapped["ResumeMetadata"] = relationship(back_populates="resumes")
    parent: Mapped[Optional["Resume"]] = relationship(
        remote_side=[version, user_id, job_id],
        foreign_keys=[parent_version],
        primaryjoin="and_(Resume.parent_version==Resume.version, Resume.user_id==Resume.user_id, Resume.job_id==Resume.job_id)"
    )