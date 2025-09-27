from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column
import uuid

from ..base import Base

if TYPE_CHECKING:
    from ..profile.user import ProfileUser
    from .job import Job


from pydantic import BaseModel, PrivateAttr


class ResumeSkillSchema(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    job_id: uuid.UUID
    parent_id: uuid.UUID | None = None
    skill_name: str
    skill_category: str | None = None
    proficiency_level: str | None = None
    _orm_entity: Optional["ResumeSkill"] = PrivateAttr(default=None)

    class Config:
        from_attributes = True


class ResumeSkill(Base):
    __tablename__ = "resume_skills"

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
        UUID(as_uuid=True), ForeignKey("resume_skills.id"), nullable=True
    )
    skill_name: Mapped[str] = mapped_column(String, nullable=False)
    skill_category: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    proficiency_level: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    __table_args__ = (
        UniqueConstraint("user_id", "job_id", name="uq_resume_skill_user_job"),
    )

    # Relationships
    user: Mapped["ProfileUser"] = relationship(foreign_keys=[user_id])
    job: Mapped["Job"] = relationship(back_populates="resume_skills")
    parent: Mapped[Optional["ResumeSkill"]] = relationship(
        remote_side=[id], foreign_keys=[parent_id]
    )

    @property
    def schema(self):
        result = ResumeSkillSchema.model_validate(self)
        result._orm_entity = self
        return result
