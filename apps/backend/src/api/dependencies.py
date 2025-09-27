"""API dependencies for dependency injection."""

import uuid
from typing import Optional
from fastapi import Depends, HTTPException, status, Header
from fastapi.security import (
    HTTPBearer,
    HTTPAuthorizationCredentials,
    OAuth2PasswordBearer,
)
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy import select
from dependency_injector.wiring import inject, Provide
import hashlib

from src.containers import Container
from src.core.security import SecurityUtils
from src.core.unit_of_work import UnitOfWorkFactory
from src.models.auth import TokenPayload
from src.config.auth import AuthConfig
from src.models.db.auth.api_key import APIKey
import redis.asyncio as redis

from src.models.db.profile.user import ProfileUserSchema


# Security schemes
security_scheme = HTTPBearer(auto_error=False)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token", auto_error=False)


# @inject
# async def get_db(
#     session_factory=Provide[Container.async_session_factory],
# ) -> AsyncGenerator[AsyncSession, None]:
#     """Get database session."""
#     async with session_factory() as session:
#         yield session


@inject
def get_redis_client(
    redis_client: redis.Redis = Provide[Container.redis_client],
) -> redis.Redis:
    """Get Redis client."""
    return redis_client


@inject
def _get_auth_config(
    jwt_secret_key=Provide[Container.config.auth.jwt_secret_key],
    jwt_algorithm=Provide[Container.config.auth.jwt_algorithm],
    access_token_expire_minutes=Provide[
        Container.config.auth.access_token_expire_minutes
    ],
    refresh_token_expire_days=Provide[Container.config.auth.refresh_token_expire_days],
    password_reset_token_expire_hours=Provide[
        Container.config.auth.password_reset_token_expire_hours
    ],
    email_verification_token_expire_hours=Provide[
        Container.config.auth.email_verification_token_expire_hours
    ],
) -> AuthConfig:
    """Get authentication configuration."""
    return AuthConfig(
        jwt_secret_key=jwt_secret_key,
        jwt_algorithm=jwt_algorithm or "HS256",
        access_token_expire_minutes=int(access_token_expire_minutes or 30),
        refresh_token_expire_days=int(refresh_token_expire_days or 7),
        password_reset_token_expire_hours=int(password_reset_token_expire_hours or 24),
        email_verification_token_expire_hours=int(
            email_verification_token_expire_hours or 48
        ),
    )


def get_auth_config() -> AuthConfig:
    """Get authentication configuration."""
    return _get_auth_config()


async def get_security_utils(
    config: AuthConfig = Depends(get_auth_config),
) -> SecurityUtils:
    """Get security utilities."""
    return SecurityUtils(config)


@inject
def get_session_maker(
    session_maker: async_sessionmaker = Provide[Container.async_session_factory],
) -> async_sessionmaker:
    """Get session maker."""
    return session_maker


async def get_current_token(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    oauth2_token: Optional[str] = Depends(oauth2_scheme),
    security: SecurityUtils = Depends(get_security_utils),
) -> TokenPayload:
    """Extract and validate current token from either HTTPBearer or OAuth2."""
    # Try to get token from HTTPBearer first, then OAuth2
    token = None
    if credentials and credentials.credentials:
        token = credentials.credentials
    elif oauth2_token:
        token = oauth2_token

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Decode token
    token_payload = security.decode_token(token)
    if not token_payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if token is an access token
    if token_payload.token_type != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if token is blacklisted
    async with UnitOfWorkFactory() as uow:
        repository = uow.auth_repository
        if token_payload.jti is not None and await repository.is_token_blacklisted(
            token_payload.jti
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been revoked",
                headers={"WWW-Authenticate": "Bearer"},
            )
        elif token_payload.jti is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing jti",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Check if token is expired
        if security.is_token_expired(token_payload):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return token_payload


async def get_current_user(
    token_payload: TokenPayload = Depends(get_current_token),
) -> ProfileUserSchema:
    """Get current authenticated user."""
    # Get user from database
    async with UnitOfWorkFactory() as uow:
        user = await uow.auth_repository.get_user_by_id(token_payload.sub)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        # Convert to response schema
        return user.schema


async def get_current_active_user(
    current_user: ProfileUserSchema = Depends(get_current_user),
) -> ProfileUserSchema:
    """Get current active user."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user"
        )
    return current_user


async def get_current_user_id(
    current_user: ProfileUserSchema = Depends(get_current_user),
) -> uuid.UUID:
    """Get current user's ID."""
    return current_user.id


async def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    security: SecurityUtils = Depends(get_security_utils),
) -> Optional[ProfileUserSchema]:
    """Get current user if authenticated, otherwise None."""
    if not credentials:
        return None

    try:
        token_payload = await get_current_token(credentials, security=security)
        return await get_current_user(token_payload)
    except HTTPException:
        return None


async def verify_api_key(
    api_key: Optional[str] = Header(None, alias="X-API-Key"),
) -> bool:
    """Check if API key is valid."""
    if not api_key:
        return False

    session_maker = get_session_maker()

    key_hash = hashlib.sha256(api_key.encode()).hexdigest()
    async with session_maker() as db:
        result = await db.execute(
            select(APIKey).where(APIKey.key_hash == key_hash, APIKey.is_active)
        )

        return result.scalar_one_or_none() is not None


async def require_api_key(valid_key: bool = Depends(verify_api_key)):
    """Require valid API key for endpoint."""
    if not valid_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
            headers={"WWW-Authenticate": "X-API-Key"},
        )


async def require_any_auth(
    jwt_user: Optional[ProfileUserSchema] = Depends(get_optional_current_user),
    api_key_valid: bool = Depends(verify_api_key),
):
    """Require either JWT or API key authentication."""
    if not jwt_user and not api_key_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer, X-API-Key"},
        )
