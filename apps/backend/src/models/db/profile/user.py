import datetime
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column
import uuid

from ..base import Base

if TYPE_CHECKING:
    from .education import ProfileEducation
    from .work import ProfileWorkExperience
    from .project import ProfileProject
    from .skill import ProfileUserSkill
    from ..auth.auth_provider import AuthProvider
    from ..auth.refresh_token import RefreshToken
    from ..auth.user_session import UserSession
    from ..auth.blacklisted_token import BlacklistedToken
    from ..auth.password_reset_token import PasswordResetToken
    from ..auth.email_verification_token import EmailVerificationToken


from pydantic import BaseModel, PrivateAttr


class ProfileUserSchema(BaseModel):
    id: uuid.UUID
    first_name: str
    full_name: str | None = None
    last_name: str | None = None
    name_prefix: str | None = None
    name_suffix: str | None = None
    email: str
    email_verified: bool
    email_verified_at: datetime.datetime | None = None
    phone: str | None = None
    location: str | None = None
    avatar_url: str | None = None
    linkedin_url: str | None = None
    github_url: str | None = None
    portfolio_url: str | None = None
    is_active: bool
    last_login_at: datetime.datetime | None = None
    created_at: datetime.datetime
    updated_at: datetime.datetime
    _orm_entity: Optional["ProfileUser"] = PrivateAttr(default=None)

    class Config:
        from_attributes = True


class ProfileUser(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    first_name: Mapped[str] = mapped_column(String, nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    name_prefix: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    name_suffix: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    email: Mapped[str] = mapped_column(String, nullable=False, unique=True)

    email_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    email_verified_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    phone: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    location: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    avatar_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    linkedin_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    github_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    portfolio_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    # Auth-related fields
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    last_login_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
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
    educations: Mapped[List["ProfileEducation"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    work_experiences: Mapped[List["ProfileWorkExperience"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    projects: Mapped[List["ProfileProject"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    user_skills: Mapped[List["ProfileUserSkill"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )

    # Auth relationships
    auth_providers: Mapped[List["AuthProvider"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    refresh_tokens: Mapped[List["RefreshToken"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    sessions: Mapped[List["UserSession"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    blacklisted_tokens: Mapped[List["BlacklistedToken"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    password_reset_tokens: Mapped[List["PasswordResetToken"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    email_verification_tokens: Mapped[List["EmailVerificationToken"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )

    @property
    def schema(self):
        result = ProfileUserSchema.model_validate(self)
        result._orm_entity = self
        return result
