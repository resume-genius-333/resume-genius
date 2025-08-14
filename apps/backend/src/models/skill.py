# pyright: reportMissingTypeStubs=false
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String, ForeignKey, Enum, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column
from pgvector.sqlalchemy import Vector
import uuid

from .base import Base
from .enums import SkillCategory, ProficiencyLevel

if TYPE_CHECKING:
    from .user import User
    from .project import ProjectTask
    from .work import WorkResponsibility


class Skill(Base):
    __tablename__ = "skills"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    skill_name: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    skill_category: Mapped[SkillCategory] = mapped_column(Enum(SkillCategory), nullable=False)
    embedding: Mapped[List[float]] = mapped_column(Vector(1536), nullable=False)  # OpenAI embeddings are 1536 dimensions

    # Relationships
    user_skills: Mapped[List["UserSkill"]] = relationship(back_populates="skill", cascade="all, delete-orphan")


class UserSkill(Base):
    __tablename__ = "user_skills"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)
    skill_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("skills.id"), primary_key=True)
    proficiency_level: Mapped[Optional[ProficiencyLevel]] = mapped_column(Enum(ProficiencyLevel), nullable=True)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="user_skills")
    skill: Mapped["Skill"] = relationship(back_populates="user_skills")
    task_mappings: Mapped[List["TaskSkillMapping"]] = relationship(
        back_populates="user_skill", cascade="all, delete-orphan"
    )
    responsibility_mappings: Mapped[List["ResponsibilitySkillMapping"]] = relationship(
        back_populates="user_skill", cascade="all, delete-orphan"
    )


class TaskSkillMapping(Base):
    __tablename__ = "task_skill_mappings"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)
    skill_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("skills.id"), primary_key=True)
    task_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("project_tasks.id"), primary_key=True)
    justification: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    __table_args__ = (
        UniqueConstraint('user_id', 'skill_id', 'task_id', name='uq_task_skill_mapping'),
    )

    # Relationships
    user_skill: Mapped["UserSkill"] = relationship(
        foreign_keys=[user_id, skill_id], 
        primaryjoin="and_(TaskSkillMapping.user_id==UserSkill.user_id, TaskSkillMapping.skill_id==UserSkill.skill_id)"
    )
    task: Mapped["ProjectTask"] = relationship(back_populates="skill_mappings")


class ResponsibilitySkillMapping(Base):
    __tablename__ = "responsibility_skill_mappings"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)
    skill_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("skills.id"), primary_key=True)
    responsibility_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("work_responsibilities.id"), primary_key=True
    )
    justification: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    __table_args__ = (
        UniqueConstraint('user_id', 'skill_id', 'responsibility_id', name='uq_responsibility_skill_mapping'),
    )

    # Relationships
    user_skill: Mapped["UserSkill"] = relationship(
        foreign_keys=[user_id, skill_id],
        primaryjoin="and_(ResponsibilitySkillMapping.user_id==UserSkill.user_id, ResponsibilitySkillMapping.skill_id==UserSkill.skill_id)"
    )
    responsibility: Mapped["WorkResponsibility"] = relationship(back_populates="skill_mappings")