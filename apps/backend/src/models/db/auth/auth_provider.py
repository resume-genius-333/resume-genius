import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import Boolean, DateTime, String, Integer, ForeignKey, Enum, JSON, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column
import uuid

from ..base import Base
from .enums import ProviderType

if TYPE_CHECKING:
    from ..user import User


class AuthProvider(Base):
    __tablename__ = "auth_providers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    provider_type: Mapped[ProviderType] = mapped_column(Enum(ProviderType), nullable=False)
    provider_user_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)  # Nullable for password type
    provider_email: Mapped[Optional[str]] = mapped_column(String, nullable=True)  # Email from provider
    password_hash: Mapped[Optional[str]] = mapped_column(String, nullable=True)  # Only for password type
    
    # Security fields
    failed_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    locked_until: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # OAuth token fields
    access_token: Mapped[Optional[str]] = mapped_column(String, nullable=True)  # Encrypted
    refresh_token: Mapped[Optional[str]] = mapped_column(String, nullable=True)  # Encrypted
    token_expires_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Provider-specific data
    provider_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Status fields
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    last_used_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    # Relationships
    user: Mapped["User"] = relationship(back_populates="auth_providers")