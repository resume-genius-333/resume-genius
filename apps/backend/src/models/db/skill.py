# pyright: reportMissingTypeStubs=false
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String, ForeignKey, Enum, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column
from pgvector.sqlalchemy import Vector
import uuid

from src.models.llm.skill import SkillLLMSchema

from .base import Base
from .enums import SkillCategory, ProficiencyLevel

if TYPE_CHECKING:
    from .user import User
    from .project import ProjectTask
    from .work import WorkResponsibility


from pydantic import BaseModel, PrivateAttr


class SkillSchema(BaseModel):
    id: uuid.UUID
    skill_name: str
    skill_category: SkillCategory
    embedding: List[float]
    _orm_entity: Optional["Skill"] = PrivateAttr(default=None)

    class Config:
        from_attributes = True


class Skill(Base):
    __tablename__ = "skills"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    skill_name: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    skill_category: Mapped[SkillCategory] = mapped_column(
        Enum(SkillCategory), nullable=False
    )
    embedding: Mapped[List[float]] = mapped_column(
        Vector(1536), nullable=False
    )  # OpenAI embeddings are 1536 dimensions

    # Relationships
    user_skills: Mapped[List["UserSkill"]] = relationship(
        back_populates="skill", cascade="all, delete-orphan"
    )

    @staticmethod
    def from_llm(
        skill_id: str | uuid.UUID,
        llm_schema: SkillLLMSchema,
        embedding: List[float],
    ):
        if isinstance(skill_id, str):
            skill_id = uuid.UUID(skill_id)
        return Skill(
            id=skill_id,
            skill_name=llm_schema.skill_name,
            skill_category=llm_schema.skill_category,
            embedding=embedding,
        )

    @property
    def schema(self):
        result = SkillSchema.model_validate(self)
        result._orm_entity = self
        return result


class UserSkillSchema(BaseModel):
    user_id: uuid.UUID
    skill_id: uuid.UUID
    proficiency_level: ProficiencyLevel | None = None
    _orm_entity: Optional["UserSkill"] = PrivateAttr(default=None)

    class Config:
        from_attributes = True


class UserSkill(Base):
    __tablename__ = "user_skills"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True
    )
    skill_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("skills.id"), primary_key=True
    )
    proficiency_level: Mapped[Optional[ProficiencyLevel]] = mapped_column(
        Enum(ProficiencyLevel), nullable=True
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="user_skills")
    skill: Mapped["Skill"] = relationship(back_populates="user_skills")
    task_mappings: Mapped[List["TaskSkillMapping"]] = relationship(
        primaryjoin="and_(UserSkill.user_id==foreign(TaskSkillMapping.user_id), UserSkill.skill_id==foreign(TaskSkillMapping.skill_id))",
        back_populates="user_skill",
        cascade="all, delete-orphan",
        viewonly=True,
    )
    responsibility_mappings: Mapped[List["ResponsibilitySkillMapping"]] = relationship(
        primaryjoin="and_(UserSkill.user_id==foreign(ResponsibilitySkillMapping.user_id), UserSkill.skill_id==foreign(ResponsibilitySkillMapping.skill_id))",
        back_populates="user_skill",
        cascade="all, delete-orphan",
        viewonly=True,
    )

    @property
    def schema(self):
        result = UserSkillSchema.model_validate(self)
        result._orm_entity = self
        return result


class TaskSkillMappingSchema(BaseModel):
    user_id: uuid.UUID
    skill_id: uuid.UUID
    task_id: uuid.UUID
    justification: str | None = None
    _orm_entity: Optional["TaskSkillMapping"] = PrivateAttr(default=None)

    class Config:
        from_attributes = True


class TaskSkillMapping(Base):
    __tablename__ = "task_skill_mappings"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True
    )
    skill_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("skills.id"), primary_key=True
    )
    task_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("project_tasks.id"), primary_key=True
    )
    justification: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    __table_args__ = (
        UniqueConstraint(
            "user_id", "skill_id", "task_id", name="uq_task_skill_mapping"
        ),
    )

    # Relationships
    user_skill: Mapped["UserSkill"] = relationship(
        foreign_keys=[user_id, skill_id],
        primaryjoin="and_(TaskSkillMapping.user_id==UserSkill.user_id, TaskSkillMapping.skill_id==UserSkill.skill_id)",
        back_populates="task_mappings",
    )
    task: Mapped["ProjectTask"] = relationship(back_populates="skill_mappings")

    @property
    def schema(self):
        result = TaskSkillMappingSchema.model_validate(self)
        result._orm_entity = self
        return result


class ResponsibilitySkillMappingSchema(BaseModel):
    user_id: uuid.UUID
    skill_id: uuid.UUID
    responsibility_id: uuid.UUID
    justification: str | None = None
    _orm_entity: Optional["ResponsibilitySkillMapping"] = PrivateAttr(default=None)

    class Config:
        from_attributes = True


class ResponsibilitySkillMapping(Base):
    __tablename__ = "responsibility_skill_mappings"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True
    )
    skill_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("skills.id"), primary_key=True
    )
    responsibility_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("work_responsibilities.id"), primary_key=True
    )
    justification: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "skill_id",
            "responsibility_id",
            name="uq_responsibility_skill_mapping",
        ),
    )

    # Relationships
    user_skill: Mapped["UserSkill"] = relationship(
        foreign_keys=[user_id, skill_id],
        primaryjoin="and_(ResponsibilitySkillMapping.user_id==UserSkill.user_id, ResponsibilitySkillMapping.skill_id==UserSkill.skill_id)",
        back_populates="responsibility_mappings",
    )
    responsibility: Mapped["WorkResponsibility"] = relationship(
        back_populates="skill_mappings"
    )

    @property
    def schema(self):
        result = ResponsibilitySkillMappingSchema.model_validate(self)
        result._orm_entity = self
        return result
