from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column
import uuid

from ..base import Base

if TYPE_CHECKING:
    from ..user import User
    from .resume import Resume
    from .resume_metadata import ResumeMetadata
    from .resume_education import ResumeEducation
    from .resume_work_experience import ResumeWorkExperience
    from .resume_project import ResumeProject
    from .resume_skill import ResumeSkill


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    company_name: Mapped[str] = mapped_column(String, nullable=False)
    position_title: Mapped[str] = mapped_column(String, nullable=False)
    job_description: Mapped[str] = mapped_column(Text, nullable=False)
    job_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    # Relationships
    user: Mapped["User"] = relationship(foreign_keys=[user_id])
    resumes: Mapped[List["Resume"]] = relationship(back_populates="job", cascade="all, delete-orphan")
    resume_metadata: Mapped[List["ResumeMetadata"]] = relationship(back_populates="job", cascade="all, delete-orphan")
    resume_educations: Mapped[List["ResumeEducation"]] = relationship(back_populates="job", cascade="all, delete-orphan")
    resume_work_experiences: Mapped[List["ResumeWorkExperience"]] = relationship(
        back_populates="job", cascade="all, delete-orphan"
    )
    resume_projects: Mapped[List["ResumeProject"]] = relationship(back_populates="job", cascade="all, delete-orphan")
    resume_skills: Mapped[List["ResumeSkill"]] = relationship(back_populates="job", cascade="all, delete-orphan")