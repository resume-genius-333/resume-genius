import datetime
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import Boolean, DateTime, String, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column
import uuid

from ..base import Base

if TYPE_CHECKING:
    from ..profile.user import ProfileUser
    from .user_session import UserSession


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    token_hash: Mapped[str] = mapped_column(String, nullable=False)  # Hashed JWT refresh token
    
    # Device information
    device_info: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    ip_address: Mapped[str] = mapped_column(String, nullable=False)
    user_agent: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    
    # Token lifecycle
    expires_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_used_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    is_revoked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    # Relationships
    user: Mapped["ProfileUser"] = relationship(back_populates="refresh_tokens")
    sessions: Mapped[List["UserSession"]] = relationship(back_populates="refresh_token", cascade="all, delete-orphan")
