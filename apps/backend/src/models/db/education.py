from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Float, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column
import uuid

from src.models.llm.education import EducationLLMSchema

from .base import Base
from .enums import DegreeType

if TYPE_CHECKING:
    from .user import User


from pydantic import BaseModel, PrivateAttr


class EducationSchema(BaseModel):
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
    _orm_entity: Optional["Education"] = PrivateAttr(default=None)

    class Config:
        from_attributes = True


class Education(Base):
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

    # Relationships
    user: Mapped["User"] = relationship(back_populates="educations")

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
        return Education(
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
        result = EducationSchema.model_validate(self)
        result._orm_entity = self
        return result
