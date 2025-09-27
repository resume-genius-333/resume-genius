"""Authentication service for business logic."""

import logging
from typing import Optional
from datetime import datetime, timezone
from uuid import UUID
from src.core.unit_of_work import UnitOfWork

from src.core.security import SecurityUtils
from src.config.auth import AuthConfig
from src.models.auth import (
    UserRegisterRequest,
    UserRegisterResponse,
    UserLoginRequest,
    UserLoginResponse,
    RefreshTokenRequest,
    RefreshTokenResponse,
)
from src.models.db import ProviderType
from src.models.db.profile.user import ProfileUserSchema


# Configure logging
logger = logging.getLogger(__name__)


class AuthService:
    """Service for authentication business logic."""

    def __init__(self, uow: UnitOfWork, security: SecurityUtils, config: AuthConfig):
        """Initialize auth service with dependencies."""
        self.uow = uow
        self.security = security
        self.config = config

    async def register_user(
        self,
        request: UserRegisterRequest,
        ip_address: str,
        user_agent: Optional[str] = None,
    ) -> UserRegisterResponse:
        """Register a new user."""
        # Check if user already exists
        existing_user = await self.uow.auth_repository.get_user_by_email(request.email)
        if existing_user:
            raise ValueError("User with this email already exists")

        # Create user
        user = await self.uow.auth_repository.create_user(
            email=request.email,
            first_name=request.first_name,
            last_name=request.last_name,
        )

        # Hash password and create auth provider
        password_hash = self.security.hash_password(request.password)
        await self.uow.auth_repository.create_auth_provider(
            user_id=user.id,
            provider_type=ProviderType.PASSWORD,
            password_hash=password_hash,
            provider_email=request.email,
        )

        # Return response
        return UserRegisterResponse(
            id=str(user.id),
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            full_name=user.full_name,
            is_active=user.is_active,
            email_verified=user.email_verified,
            created_at=user.created_at.isoformat(),
        )

    async def login_user(
        self,
        request: UserLoginRequest,
        ip_address: str,
        user_agent: Optional[str] = None,
    ) -> UserLoginResponse:
        """Authenticate user and create session."""
        logger.info(f"Login attempt for email: {request.email}")

        # Get user
        logger.debug("Fetching user from database")
        user = await self.uow.auth_repository.get_user_by_email(request.email)
        if not user:
            logger.warning(f"User not found for email: {request.email}")
            raise ValueError("Invalid email or password")
        logger.debug(f"User found: ID={user.id}, Active={user.is_active}")

        # Check if user is active
        if not user.is_active:
            logger.warning(f"Inactive user attempting login: {request.email}")
            raise ValueError("Account is deactivated")

        # Get auth provider
        logger.debug(f"Fetching auth provider for user ID: {user.id}")
        auth_provider = await self.uow.auth_repository.get_auth_provider(
            user_id=user.id, provider_type=ProviderType.PASSWORD
        )
        if not auth_provider:
            logger.warning(f"No password auth provider found for user: {user.id}")
            raise ValueError("Invalid email or password")
        logger.debug(f"Auth provider found for user: {user.id}")

        # Check if account is locked
        if auth_provider.locked_until:
            if auth_provider.locked_until > datetime.now(timezone.utc):
                raise ValueError(
                    "Account is temporarily locked due to too many failed attempts"
                )
            else:
                # Unlock if lockout period has passed
                auth_provider.locked_until = None
                auth_provider.failed_attempts = 0

        # Verify password
        logger.debug("Verifying password")
        if not auth_provider.password_hash or not self.security.verify_password(
            request.password, auth_provider.password_hash
        ):
            logger.warning(f"Invalid password for user: {request.email}")
            await self.uow.auth_repository.update_login_attempt(
                auth_provider, success=False
            )
            raise ValueError("Invalid email or password")
        logger.debug("Password verified successfully")

        # Reset failed attempts on successful login
        logger.debug("Updating login attempt as successful")
        await self.uow.auth_repository.update_login_attempt(auth_provider, success=True)

        # Generate session ID
        session_id = self.security.generate_session_id()
        logger.debug(f"Generated session ID: {session_id}")

        # Create tokens
        logger.debug("Creating access and refresh tokens")
        access_token = self.security.create_access_token(str(user.id), session_id)
        refresh_token = self.security.create_refresh_token(str(user.id), session_id)
        logger.debug("Tokens created successfully")

        # Hash refresh token for storage
        refresh_token_hash = self.security.hash_token(refresh_token)

        # Store refresh token
        logger.debug("Storing refresh token in database")
        refresh_token_model = await self.uow.auth_repository.create_refresh_token(
            user_id=user.id,
            token_hash=refresh_token_hash,
            ip_address=ip_address,
            user_agent=user_agent,
            expires_days=self.config.refresh_token_expire_days
            if not request.remember_me
            else 30,
        )
        logger.debug(f"Refresh token stored with ID: {refresh_token_model.id}")

        # Create user session
        logger.debug("Creating user session")
        await self.uow.auth_repository.create_user_session(
            user_id=user.id,
            refresh_token_id=refresh_token_model.id,
            session_id=session_id,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        logger.debug("User session created")

        # Update last login
        logger.debug("Updating last login timestamp")
        await self.uow.auth_repository.update_user_last_login(user.id)
        logger.info(f"Login successful for user: {request.email}")

        # Return response
        logger.debug("Returning login response")
        return UserLoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=self.config.access_token_expire_minutes * 60,
        )

    async def refresh_access_token(
        self,
        request: RefreshTokenRequest,
        ip_address: str,
        user_agent: Optional[str] = None,
    ) -> RefreshTokenResponse:
        """Refresh access token using refresh token."""
        # Decode refresh token
        token_payload = self.security.decode_token(request.refresh_token)
        if not token_payload or token_payload.token_type != "refresh":
            raise ValueError("Invalid refresh token")

        # Check if token is blacklisted
        if not token_payload.jti:
            raise ValueError("Invalid refresh token")
        if await self.uow.auth_repository.is_token_blacklisted(token_payload.jti):
            raise ValueError("Token has been revoked")

        # Hash token and get from database
        token_hash = self.security.hash_token(request.refresh_token)
        refresh_token_model = await self.uow.auth_repository.get_refresh_token(
            token_hash
        )
        if not refresh_token_model:
            raise ValueError("Invalid refresh token")

        # Get user
        user = await self.uow.auth_repository.get_user_by_id(token_payload.sub)
        if not user or not user.is_active:
            raise ValueError("User not found or inactive")

        # Update refresh token last used
        refresh_token_model.last_used_at = datetime.now(timezone.utc)

        # Update session activity
        if token_payload.session_id:
            await self.uow.auth_repository.update_session_activity(
                token_payload.session_id
            )

        # Create new access token
        access_token = self.security.create_access_token(
            str(user.id), token_payload.session_id
        )

        # Return response
        return RefreshTokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=self.config.access_token_expire_minutes * 60,
        )

    async def logout_user(
        self, access_token: str, refresh_token: Optional[str] = None
    ) -> None:
        """Logout user by revoking tokens and ending session."""
        # Decode access token
        access_payload = self.security.decode_token(access_token)
        if access_payload:
            # Blacklist access token
            if access_payload.jti is not None and access_payload.sub is not None:
                await self.uow.auth_repository.blacklist_token(
                    jti=access_payload.jti,
                    user_id=UUID(access_payload.sub),
                    expires_at=access_payload.exp,
                    reason="User logout",
                )

            # End session
            if access_payload.session_id:
                await self.uow.auth_repository.end_user_session(
                    access_payload.session_id
                )

        # Revoke refresh token if provided
        if refresh_token:
            refresh_payload = self.security.decode_token(refresh_token)
            if refresh_payload:
                # Blacklist refresh token
                if refresh_payload.jti is not None and refresh_payload.sub is not None:
                    await self.uow.auth_repository.blacklist_token(
                        jti=refresh_payload.jti,
                        user_id=UUID(refresh_payload.sub),
                        expires_at=refresh_payload.exp,
                        reason="User logout",
                    )

                # Revoke refresh token in database
                token_hash = self.security.hash_token(refresh_token)
                await self.uow.auth_repository.revoke_refresh_token(token_hash)

    async def get_current_user(self, user_id: str) -> ProfileUserSchema:
        """Get current user information."""
        user = await self.uow.auth_repository.get_user_by_id(user_id)
        if not user:
            raise ValueError("User not found")

        return user.schema
