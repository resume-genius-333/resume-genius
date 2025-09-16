from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column
import uuid

from src.models.llm.work import WorkExperienceLLMSchema, WorkResponsibilityLLMSchema

from .base import Base
from .enums import EmploymentType

if TYPE_CHECKING:
    from .user import User
    from .skill import ResponsibilitySkillMapping


from pydantic import BaseModel, PrivateAttr


class WorkExperienceSchema(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    company_name: str
    position_title: str
    employment_type: EmploymentType
    location: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    _orm_entity: Optional["WorkExperience"] = PrivateAttr(default=None)

    class Config:
        from_attributes = True


class WorkExperience(Base):
    __tablename__ = "work_experiences"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    company_name: Mapped[str] = mapped_column(String, nullable=False)
    position_title: Mapped[str] = mapped_column(String, nullable=False)
    employment_type: Mapped[EmploymentType] = mapped_column(
        Enum(EmploymentType), nullable=False
    )
    location: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    start_date: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    end_date: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="work_experiences")
    responsibilities: Mapped[List["WorkResponsibility"]] = relationship(
        back_populates="work_experience", cascade="all, delete-orphan"
    )

    @staticmethod
    def from_llm(
        user_id: str | uuid.UUID,
        work_id: str | uuid.UUID,
        llm_schema: WorkExperienceLLMSchema,
    ):
        if isinstance(user_id, str):
            user_id = uuid.UUID(user_id)
        if isinstance(work_id, str):
            work_id = uuid.UUID(work_id)
        return WorkExperience(
            id=work_id,
            user_id=user_id,
            company_name=llm_schema.company_name,
            position_title=llm_schema.position_title,
            employment_type=llm_schema.employment_type,
            location=llm_schema.location,
            start_date=llm_schema.start_date,
            end_date=llm_schema.end_date,
        )

    @property
    def schema(self):
        result = WorkExperienceSchema.model_validate(self)
        result._orm_entity = self
        return result


class WorkResponsibilitySchema(BaseModel):
    id: uuid.UUID
    work_id: uuid.UUID
    user_id: uuid.UUID
    description: str
    _orm_entity: Optional["WorkResponsibility"] = PrivateAttr(default=None)

    class Config:
        from_attributes = True


class WorkResponsibility(Base):
    __tablename__ = "work_responsibilities"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    work_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("work_experiences.id"), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    description: Mapped[str] = mapped_column(String, nullable=False)

    # Relationships
    work_experience: Mapped["WorkExperience"] = relationship(
        back_populates="responsibilities"
    )
    skill_mappings: Mapped[List["ResponsibilitySkillMapping"]] = relationship(
        back_populates="responsibility", cascade="all, delete-orphan"
    )

    @staticmethod
    def from_llm(
        user_id: str | uuid.UUID,
        work_id: str | uuid.UUID,
        responsibility_id: str | uuid.UUID,
        llm_schema: WorkResponsibilityLLMSchema,
    ):
        if isinstance(user_id, str):
            user_id = uuid.UUID(user_id)
        if isinstance(work_id, str):
            work_id = uuid.UUID(work_id)
        if isinstance(responsibility_id, str):
            responsibility_id = uuid.UUID(responsibility_id)
        return WorkResponsibility(
            id=responsibility_id,
            work_id=work_id,
            user_id=user_id,
            description=llm_schema.description,
        )

    @property
    def schema(self):
        result = WorkResponsibilitySchema.model_validate(self)
        result._orm_entity = self
        return result
