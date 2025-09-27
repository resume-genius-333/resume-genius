# pyright: reportMissingTypeStubs=false
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String, ForeignKey, Enum, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column
from pgvector.sqlalchemy import Vector
import uuid

from src.models.llm.skill import SkillLLMSchema

from ..base import Base
from ..enums import SkillCategory, ProficiencyLevel

if TYPE_CHECKING:
    from .user import ProfileUser
    from .project import ProfileProjectTask
    from .work import ProfileWorkResponsibility


from pydantic import BaseModel, PrivateAttr


class ProfileSkillSchema(BaseModel):
    id: uuid.UUID
    skill_name: str
    skill_category: SkillCategory
    embedding: List[float]
    _orm_entity: Optional["ProfileSkill"] = PrivateAttr(default=None)

    class Config:
        from_attributes = True


class ProfileSkill(Base):
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
    user_skills: Mapped[List["ProfileUserSkill"]] = relationship(
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
        return ProfileSkill(
            id=skill_id,
            skill_name=llm_schema.skill_name,
            skill_category=llm_schema.skill_category,
            embedding=embedding,
        )

    @property
    def schema(self):
        result = ProfileSkillSchema.model_validate(self)
        result._orm_entity = self
        return result


class ProfileUserSkillSchema(BaseModel):
    user_id: uuid.UUID
    skill_id: uuid.UUID
    proficiency_level: ProficiencyLevel | None = None
    _orm_entity: Optional["ProfileUserSkill"] = PrivateAttr(default=None)

    class Config:
        from_attributes = True


class ProfileUserSkill(Base):
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
    user: Mapped["ProfileUser"] = relationship(back_populates="user_skills")
    skill: Mapped["ProfileSkill"] = relationship(back_populates="user_skills")
    task_mappings: Mapped[List["ProfileTaskSkillMapping"]] = relationship(
        primaryjoin="and_(ProfileUserSkill.user_id==foreign(ProfileTaskSkillMapping.user_id), ProfileUserSkill.skill_id==foreign(ProfileTaskSkillMapping.skill_id))",
        back_populates="user_skill",
        cascade="all, delete-orphan",
        viewonly=True,
    )
    responsibility_mappings: Mapped[List["ProfileResponsibilitySkillMapping"]] = (
        relationship(
            primaryjoin="and_(ProfileUserSkill.user_id==foreign(ProfileResponsibilitySkillMapping.user_id), ProfileUserSkill.skill_id==foreign(ProfileResponsibilitySkillMapping.skill_id))",
            back_populates="user_skill",
            cascade="all, delete-orphan",
            viewonly=True,
        )
    )

    @property
    def schema(self):
        result = ProfileUserSkillSchema.model_validate(self)
        result._orm_entity = self
        return result


class ProfileTaskSkillMappingSchema(BaseModel):
    user_id: uuid.UUID
    skill_id: uuid.UUID
    task_id: uuid.UUID
    justification: str | None = None
    _orm_entity: Optional["ProfileTaskSkillMapping"] = PrivateAttr(default=None)

    class Config:
        from_attributes = True


class ProfileTaskSkillMapping(Base):
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
    user_skill: Mapped["ProfileUserSkill"] = relationship(
        foreign_keys=[user_id, skill_id],
        primaryjoin="and_(ProfileTaskSkillMapping.user_id==ProfileUserSkill.user_id, ProfileTaskSkillMapping.skill_id==ProfileUserSkill.skill_id)",
        back_populates="task_mappings",
    )
    task: Mapped["ProfileProjectTask"] = relationship(back_populates="skill_mappings")

    @property
    def schema(self):
        result = ProfileTaskSkillMappingSchema.model_validate(self)
        result._orm_entity = self
        return result


class ProfileResponsibilitySkillMappingSchema(BaseModel):
    user_id: uuid.UUID
    skill_id: uuid.UUID
    responsibility_id: uuid.UUID
    justification: str | None = None
    _orm_entity: Optional["ProfileResponsibilitySkillMapping"] = PrivateAttr(
        default=None
    )

    class Config:
        from_attributes = True


class ProfileResponsibilitySkillMapping(Base):
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
    user_skill: Mapped["ProfileUserSkill"] = relationship(
        foreign_keys=[user_id, skill_id],
        primaryjoin="and_(ProfileResponsibilitySkillMapping.user_id==ProfileUserSkill.user_id, ProfileResponsibilitySkillMapping.skill_id==ProfileUserSkill.skill_id)",
        back_populates="responsibility_mappings",
    )
    responsibility: Mapped["ProfileWorkResponsibility"] = relationship(
        back_populates="skill_mappings"
    )

    @property
    def schema(self):
        result = ProfileResponsibilitySkillMappingSchema.model_validate(self)
        result._orm_entity = self
        return result
