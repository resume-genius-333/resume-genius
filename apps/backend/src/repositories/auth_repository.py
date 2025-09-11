"""Authentication repository for database operations."""

import logging
from typing import Optional
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
import uuid
from src.models.db import (
    User,
    AuthProvider,
    RefreshToken,
    UserSession,
    BlacklistedToken,
    ProviderType,
)


# Configure logging
logger = logging.getLogger(__name__)


class AuthRepository:
    """Repository for authentication-related database operations."""

    def __init__(self, session: AsyncSession):
        """Initialize repository with database session."""
        self.session = session

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email address."""
        logger.debug(f"Fetching user by email: {email}")
        try:
            result = await self.session.execute(select(User).where(User.email == email))
            user = result.scalar_one_or_none()
            if user:
                logger.debug(f"User found with ID: {user.id}")
            else:
                logger.debug(f"No user found with email: {email}")
            return user
        except Exception as e:
            logger.error(
                f"Error fetching user by email {email}: {str(e)}", exc_info=True
            )
            raise

    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        result = await self.session.execute(
            select(User).where(User.id == uuid.UUID(user_id))
        )
        return result.scalar_one_or_none()

    async def create_user(
        self,
        email: str,
        first_name: str,
        last_name: Optional[str] = None,
        full_name: Optional[str] = None,
    ) -> User:
        """Create a new user."""
        user = User(
            email=email,
            first_name=first_name,
            last_name=last_name,
            full_name=full_name or f"{first_name} {last_name}".strip(),
            is_active=True,
            email_verified=False,
        )
        self.session.add(user)
        await self.session.flush()
        return user

    async def create_auth_provider(
        self,
        user_id: uuid.UUID,
        provider_type: ProviderType,
        password_hash: Optional[str] = None,
        provider_user_id: Optional[str] = None,
        provider_email: Optional[str] = None,
    ) -> AuthProvider:
        """Create an auth provider for a user."""
        auth_provider = AuthProvider(
            user_id=user_id,
            provider_type=provider_type,
            password_hash=password_hash,
            provider_user_id=provider_user_id,
            provider_email=provider_email,
            is_active=True,
        )
        self.session.add(auth_provider)
        await self.session.flush()
        return auth_provider

    async def get_auth_provider(
        self, user_id: uuid.UUID, provider_type: ProviderType
    ) -> Optional[AuthProvider]:
        """Get auth provider for a user."""
        logger.debug(
            f"Fetching auth provider for user_id: {user_id}, provider_type: {provider_type}"
        )
        try:
            result = await self.session.execute(
                select(AuthProvider).where(
                    and_(
                        AuthProvider.user_id == user_id,
                        AuthProvider.provider_type == provider_type,
                        AuthProvider.is_active,
                    )
                )
            )
            provider = result.scalar_one_or_none()
            if provider:
                logger.debug(f"Auth provider found for user_id: {user_id}")
            else:
                logger.debug(f"No auth provider found for user_id: {user_id}")
            return provider
        except Exception as e:
            logger.error(
                f"Error fetching auth provider for user_id {user_id}: {str(e)}",
                exc_info=True,
            )
            raise

    async def update_login_attempt(
        self, auth_provider: AuthProvider, success: bool
    ) -> None:
        """Update login attempt count and lockout status."""
        if success:
            auth_provider.failed_attempts = 0
            auth_provider.locked_until = None
            auth_provider.last_used_at = datetime.now(timezone.utc)
        else:
            auth_provider.failed_attempts += 1
            if auth_provider.failed_attempts >= 5:  # Configurable
                auth_provider.locked_until = datetime.now(timezone.utc) + timedelta(
                    minutes=30
                )
        await self.session.flush()

    async def create_refresh_token(
        self,
        user_id: uuid.UUID,
        token_hash: str,
        ip_address: str,
        user_agent: Optional[str] = None,
        device_info: Optional[str] = None,
        expires_days: int = 7,
    ) -> RefreshToken:
        """Create a refresh token."""
        refresh_token = RefreshToken(
            user_id=user_id,
            token_hash=token_hash,
            ip_address=ip_address,
            user_agent=user_agent,
            device_info=device_info,
            expires_at=datetime.now(timezone.utc) + timedelta(days=expires_days),
            is_revoked=False,
        )
        self.session.add(refresh_token)
        await self.session.flush()
        return refresh_token

    async def get_refresh_token(self, token_hash: str) -> Optional[RefreshToken]:
        """Get refresh token by hash."""
        result = await self.session.execute(
            select(RefreshToken).where(
                and_(
                    RefreshToken.token_hash == token_hash,
                    ~RefreshToken.is_revoked,
                    RefreshToken.expires_at > datetime.now(timezone.utc),
                )
            )
        )
        return result.scalar_one_or_none()

    async def revoke_refresh_token(self, token_hash: str) -> None:
        """Revoke a refresh token."""
        result = await self.session.execute(
            select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        )
        refresh_token = result.scalar_one_or_none()
        if refresh_token:
            refresh_token.is_revoked = True
        await self.session.flush()

    async def create_user_session(
        self,
        user_id: uuid.UUID,
        refresh_token_id: uuid.UUID,
        session_id: str,
        ip_address: str,
        user_agent: Optional[str] = None,
    ) -> UserSession:
        """Create a user session."""
        user_session = UserSession(
            user_id=user_id,
            refresh_token_id=refresh_token_id,
            session_id=session_id,
            ip_address=ip_address,
            user_agent=user_agent,
            last_activity_at=datetime.now(timezone.utc),
        )
        self.session.add(user_session)
        await self.session.flush()
        return user_session

    async def get_user_session(self, session_id: str) -> Optional[UserSession]:
        """Get user session by ID."""
        result = await self.session.execute(
            select(UserSession).where(
                and_(
                    UserSession.session_id == session_id,
                    UserSession.signed_out_at.is_(None),
                )
            )
        )
        return result.scalar_one_or_none()

    async def update_session_activity(self, session_id: str) -> None:
        """Update session last activity timestamp."""
        result = await self.session.execute(
            select(UserSession).where(UserSession.session_id == session_id)
        )
        session_activity = result.scalar_one_or_none()
        if session_activity:
            session_activity.last_activity_at = datetime.now(timezone.utc)
            await self.session.flush()

    async def end_user_session(self, session_id: str) -> None:
        """End a user session."""
        result = await self.session.execute(
            select(UserSession).where(UserSession.session_id == session_id)
        )
        session_activity = result.scalar_one_or_none()
        if session_activity:
            session_activity.signed_out_at = datetime.now(timezone.utc)
        await self.session.flush()

    async def blacklist_token(
        self,
        jti: str,
        user_id: uuid.UUID,
        expires_at: datetime,
        reason: Optional[str] = None,
    ) -> BlacklistedToken:
        """Add a token to the blacklist."""
        blacklisted_token = BlacklistedToken(
            jti=jti, user_id=user_id, expires_at=expires_at, reason=reason
        )
        self.session.add(blacklisted_token)
        await self.session.flush()
        return blacklisted_token

    async def is_token_blacklisted(self, jti: str) -> bool:
        """Check if a token is blacklisted."""
        result = await self.session.execute(
            select(BlacklistedToken).where(
                and_(
                    BlacklistedToken.jti == jti,
                    BlacklistedToken.expires_at > datetime.now(timezone.utc),
                )
            )
        )
        return result.scalar_one_or_none() is not None

    async def update_user_last_login(self, user_id: uuid.UUID) -> None:
        """Update user's last login timestamp."""
        result = await self.session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if user:
            user.last_login_at = datetime.now(timezone.utc)
            await self.session.flush()
