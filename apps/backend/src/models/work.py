from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column
import uuid

from .base import Base
from .enums import EmploymentType

if TYPE_CHECKING:
    from .user import User
    from .skill import ResponsibilitySkillMapping


class WorkExperience(Base):
    __tablename__ = "work_experiences"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    company_name: Mapped[str] = mapped_column(String, nullable=False)
    position_title: Mapped[str] = mapped_column(String, nullable=False)
    employment_type: Mapped[EmploymentType] = mapped_column(Enum(EmploymentType), nullable=False)
    location: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    start_date: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    end_date: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="work_experiences")
    responsibilities: Mapped[List["WorkResponsibility"]] = relationship(
        back_populates="work_experience", cascade="all, delete-orphan"
    )


class WorkResponsibility(Base):
    __tablename__ = "work_responsibilities"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    work_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("work_experiences.id"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False)

    # Relationships
    work_experience: Mapped["WorkExperience"] = relationship(back_populates="responsibilities")
    skill_mappings: Mapped[List["ResponsibilitySkillMapping"]] = relationship(
        back_populates="responsibility", cascade="all, delete-orphan"
    )