from typing import Optional, List, TYPE_CHECKING
import datetime
import uuid
from sqlalchemy import String, ForeignKey, Enum, func, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column

from src.models.llm.work import WorkExperienceLLMSchema, WorkResponsibilityLLMSchema

from ..base import Base
from ..enums import EmploymentType

if TYPE_CHECKING:
    from .user import ProfileUser
    from .skill import ProfileResponsibilitySkillMapping


from pydantic import BaseModel, Field, PrivateAttr


class ProfileWorkExperienceSchema(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    company_name: str
    position_title: str
    employment_type: EmploymentType
    location: str | None = None
    start_date: str | None = None
    end_date: str | None = None

    responsibilities: Optional[List["ProfileWorkResponsibilitySchema"]] = Field(
        default=None
    )
    """
    The responsibilities are, under the hood, representing a 
    """

    created_at: datetime.datetime
    updated_at: datetime.datetime

    _orm_entity: Optional["ProfileWorkExperience"] = PrivateAttr(default=None)

    class Config:
        from_attributes = True


class ProfileWorkExperience(Base):
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
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Relationships
    user: Mapped["ProfileUser"] = relationship(back_populates="work_experiences")
    responsibilities: Mapped[List["ProfileWorkResponsibility"]] = relationship(
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
        return ProfileWorkExperience(
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
        result = ProfileWorkExperienceSchema.model_validate(self)
        result._orm_entity = self
        return result


class ProfileWorkResponsibilitySchema(BaseModel):
    id: uuid.UUID
    work_id: uuid.UUID
    user_id: uuid.UUID
    description: str
    created_at: datetime.datetime
    updated_at: datetime.datetime
    _orm_entity: Optional["ProfileWorkResponsibility"] = PrivateAttr(default=None)

    class Config:
        from_attributes = True


class ProfileWorkResponsibility(Base):
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
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Relationships
    work_experience: Mapped["ProfileWorkExperience"] = relationship(
        back_populates="responsibilities"
    )
    skill_mappings: Mapped[List["ProfileResponsibilitySkillMapping"]] = relationship(
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
        return ProfileWorkResponsibility(
            id=responsibility_id,
            work_id=work_id,
            user_id=user_id,
            description=llm_schema.description,
        )

    @property
    def schema(self):
        result = ProfileWorkResponsibilitySchema.model_validate(self)
        result._orm_entity = self
        return result
