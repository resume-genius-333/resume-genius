from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column
import uuid

from src.models.llm.resumes.job import JobLLMSchema

from ..base import Base

if TYPE_CHECKING:
    from ..profile.user import ProfileUser
    from .resume import Resume
    from .resume_metadata import ResumeMetadata
    from .resume_education import ResumeEducation
    from .resume_work_experience import ResumeWorkExperience
    from .resume_project import ResumeProject
    from .resume_skill import ResumeSkill


from pydantic import BaseModel, PrivateAttr


class JobSchema(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    company_name: str
    position_title: str
    job_description: str
    job_url: str | None = None
    _orm_entity: Optional["Job"] = PrivateAttr(default=None)

    class Config:
        from_attributes = True  # Pydantic v2 (was orm_mode = True in v1)


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    company_name: Mapped[str] = mapped_column(String, nullable=False)
    position_title: Mapped[str] = mapped_column(String, nullable=False)
    job_description: Mapped[str] = mapped_column(Text, nullable=False)
    job_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    # Relationships
    user: Mapped["ProfileUser"] = relationship(foreign_keys=[user_id])
    resumes: Mapped[List["Resume"]] = relationship(
        back_populates="job", cascade="all, delete-orphan"
    )
    resume_metadata: Mapped[List["ResumeMetadata"]] = relationship(
        back_populates="job", cascade="all, delete-orphan"
    )
    resume_educations: Mapped[List["ResumeEducation"]] = relationship(
        back_populates="job", cascade="all, delete-orphan"
    )
    resume_work_experiences: Mapped[List["ResumeWorkExperience"]] = relationship(
        back_populates="job", cascade="all, delete-orphan"
    )
    resume_projects: Mapped[List["ResumeProject"]] = relationship(
        back_populates="job", cascade="all, delete-orphan"
    )
    resume_skills: Mapped[List["ResumeSkill"]] = relationship(
        back_populates="job", cascade="all, delete-orphan"
    )

    @staticmethod
    def from_llm(
        user_id: str | uuid.UUID,
        job_id: str | uuid.UUID,
        llm_schema: JobLLMSchema,
        job_url: Optional[str] = None,
    ):
        if isinstance(user_id, str):
            user_id = uuid.UUID(user_id)
        if isinstance(job_id, str):
            job_id = uuid.UUID(job_id)
        return Job(
            id=job_id,
            user_id=user_id,
            company_name=llm_schema.company_name,
            position_title=llm_schema.position_title,
            job_description=llm_schema.job_description,
            job_url=job_url,
        )

    @property
    def schema(self):
        result = JobSchema.model_validate(self)
        result._orm_entity = self
        return result
