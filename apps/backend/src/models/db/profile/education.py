from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Float, ForeignKey, Enum, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column
import uuid
import datetime

from src.models.llm.education import EducationLLMSchema

from ..base import Base
from ..enums import DegreeType

if TYPE_CHECKING:
    from .user import ProfileUser


from pydantic import BaseModel, PrivateAttr


class ProfileEducationSchema(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    institution_name: str
    degree: DegreeType
    field_of_study: str
    focus_area: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    gpa: float | None = None
    max_gpa: float | None = None
    created_at: datetime.datetime
    updated_at: datetime.datetime
    _orm_entity: Optional["ProfileEducation"] = PrivateAttr(default=None)

    class Config:
        from_attributes = True


class ProfileEducation(Base):
    __tablename__ = "educations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    institution_name: Mapped[str] = mapped_column(String, nullable=False)
    degree: Mapped[DegreeType] = mapped_column(Enum(DegreeType), nullable=False)
    field_of_study: Mapped[str] = mapped_column(String, nullable=False)
    focus_area: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    start_date: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    end_date: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    gpa: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    max_gpa: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
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
    user: Mapped["ProfileUser"] = relationship(back_populates="educations")

    @staticmethod
    def from_llm(
        user_id: str | uuid.UUID,
        education_id: str | uuid.UUID,
        llm_schema: EducationLLMSchema,
    ):
        if isinstance(user_id, str):
            user_id = uuid.UUID(user_id)
        if isinstance(education_id, str):
            education_id = uuid.UUID(education_id)
        return ProfileEducation(
            id=education_id,
            user_id=user_id,
            institution_name=llm_schema.institution_name,
            degree=llm_schema.degree,
            field_of_study=llm_schema.field_of_study,
            focus_area=llm_schema.focus_area,
            start_date=llm_schema.start_date,
            end_date=llm_schema.end_date,
            gpa=llm_schema.gpa,
            max_gpa=llm_schema.max_gpa,
        )

    @property
    def schema(self):
        result = ProfileEducationSchema.model_validate(self)
        result._orm_entity = self
        return result
