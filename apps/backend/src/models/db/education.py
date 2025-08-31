from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Float, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column
import uuid

from .base import Base
from .enums import DegreeType

if TYPE_CHECKING:
    from .user import User


class Education(Base):
    __tablename__ = "educations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
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