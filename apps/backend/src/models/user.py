from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column
import uuid

from .base import Base

if TYPE_CHECKING:
    from .education import Education
    from .work import WorkExperience
    from .project import Project
    from .skill import UserSkill


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    first_name: Mapped[str] = mapped_column(String, nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    name_prefix: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    name_suffix: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    email: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    phone: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    location: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    linkedin_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    github_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    portfolio_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    # Relationships
    educations: Mapped[List["Education"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    work_experiences: Mapped[List["WorkExperience"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    projects: Mapped[List["Project"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    user_skills: Mapped[List["UserSkill"]] = relationship(back_populates="user", cascade="all, delete-orphan")