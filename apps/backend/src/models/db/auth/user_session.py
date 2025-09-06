import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import DateTime, String, ForeignKey, JSON, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column
import uuid

from ..base import Base

if TYPE_CHECKING:
    from ..user import User
    from .refresh_token import RefreshToken


class UserSession(Base):
    __tablename__ = "user_sessions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    refresh_token_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("refresh_tokens.id"), nullable=False)
    session_id: Mapped[str] = mapped_column(String, nullable=False, unique=True)  # Unique session identifier
    
    # Session information
    ip_address: Mapped[str] = mapped_column(String, nullable=False)
    user_agent: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    device_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Session lifecycle
    last_activity_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    signed_out_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    # Relationships
    user: Mapped["User"] = relationship(back_populates="sessions")
    refresh_token: Mapped["RefreshToken"] = relationship(back_populates="sessions")