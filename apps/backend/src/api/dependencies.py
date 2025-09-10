"""API dependencies for dependency injection."""

from typing import AsyncGenerator, Optional
from fastapi import Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from dependency_injector.wiring import inject, Provide
import hashlib

from src.containers import Container
from src.core.security import SecurityUtils
from src.repositories.auth_repository import AuthRepository
from src.models.auth import UserResponse, TokenPayload
from src.config.auth import AuthConfig
from src.models.db.auth.api_key import APIKey


# Security schemes
security_scheme = HTTPBearer(auto_error=False)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token", auto_error=False)


@inject
async def get_db(
    session_factory=Provide[Container.async_session_factory],
) -> AsyncGenerator[AsyncSession, None]:
    """Get database session."""
    async with session_factory() as session:
        yield session


@inject
async def get_auth_config(
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


async def get_security_utils(
    config: AuthConfig = Depends(get_auth_config),
) -> SecurityUtils:
    """Get security utilities."""
    return SecurityUtils(config)


async def get_auth_repository(db: AsyncSession = Depends(get_db)) -> AuthRepository:
    """Get authentication repository."""
    return AuthRepository(db)


async def get_current_token(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    oauth2_token: Optional[str] = Depends(oauth2_scheme),
    security: SecurityUtils = Depends(get_security_utils),
    repository: AuthRepository = Depends(get_auth_repository),
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
    repository: AuthRepository = Depends(get_auth_repository),
) -> UserResponse:
    """Get current authenticated user."""
    # Get user from database
    user = await repository.get_user_by_id(token_payload.sub)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    # Convert to response schema
    return UserResponse(
        id=str(user.id),
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        full_name=user.full_name,
        name_prefix=user.name_prefix,
        name_suffix=user.name_suffix,
        phone=user.phone,
        location=user.location,
        avatar_url=user.avatar_url,
        linkedin_url=user.linkedin_url,
        github_url=user.github_url,
        portfolio_url=user.portfolio_url,
        is_active=user.is_active,
        email_verified=user.email_verified,
        email_verified_at=user.email_verified_at,
        last_login_at=user.last_login_at,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


async def get_current_active_user(
    current_user: UserResponse = Depends(get_current_user),
) -> UserResponse:
    """Get current active user."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user"
        )
    return current_user


async def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    security: SecurityUtils = Depends(get_security_utils),
    repository: AuthRepository = Depends(get_auth_repository),
) -> Optional[UserResponse]:
    """Get current user if authenticated, otherwise None."""
    if not credentials:
        return None

    try:
        token_payload = await get_current_token(credentials, security, repository)
        return await get_current_user(token_payload, repository)
    except HTTPException:
        return None


async def verify_api_key(
    api_key: Optional[str] = Header(None, alias="X-API-Key"),
    db: AsyncSession = Depends(get_db),
) -> bool:
    """Check if API key is valid."""
    if not api_key:
        return False

    key_hash = hashlib.sha256(api_key.encode()).hexdigest()

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
    jwt_user: Optional[UserResponse] = Depends(get_optional_current_user),
    api_key_valid: bool = Depends(verify_api_key),
):
    """Require either JWT or API key authentication."""
    if not jwt_user and not api_key_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer, X-API-Key"},
        )
