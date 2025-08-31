"""Authentication router."""

from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Request

from src.api.dependencies import (
    get_auth_repository,
    get_security_utils,
    get_auth_config,
    get_current_active_user,
    get_current_token,
    require_api_key,
)
from src.models.auth import (
    UserRegisterRequest,
    UserRegisterResponse,
    UserLoginRequest,
    UserLoginResponse,
    RefreshTokenRequest,
    RefreshTokenResponse,
    UserResponse,
    TokenPayload,
)
from src.services.auth_service import AuthService
from src.repositories.auth_repository import AuthRepository
from src.core.security import SecurityUtils
from src.config.auth import AuthConfig


router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post(
    "/register",
    response_model=UserRegisterResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    request: UserRegisterRequest,
    req: Request,
    repository: AuthRepository = Depends(get_auth_repository),
    security: SecurityUtils = Depends(get_security_utils),
    config: AuthConfig = Depends(get_auth_config),
) -> UserRegisterResponse:
    """Register a new user."""
    service = AuthService(repository, security, config)

    # Get client info
    ip_address = req.client.host if req.client else "127.0.0.1"
    user_agent = req.headers.get("user-agent")

    try:
        return await service.register_user(request, ip_address, user_agent)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception:
        await repository.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed",
        )


@router.post("/login", response_model=UserLoginResponse)
async def login(
    request: UserLoginRequest,
    req: Request,
    repository: AuthRepository = Depends(get_auth_repository),
    security: SecurityUtils = Depends(get_security_utils),
    config: AuthConfig = Depends(get_auth_config),
) -> UserLoginResponse:
    """Login user and create session."""
    service = AuthService(repository, security, config)

    # Get client info
    ip_address = req.client.host if req.client else "127.0.0.1"
    user_agent = req.headers.get("user-agent")

    try:
        return await service.login_user(request, ip_address, user_agent)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except Exception:
        await repository.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Login failed"
        )


@router.post("/refresh", response_model=RefreshTokenResponse)
async def refresh_token(
    request: RefreshTokenRequest,
    req: Request,
    repository: AuthRepository = Depends(get_auth_repository),
    security: SecurityUtils = Depends(get_security_utils),
    config: AuthConfig = Depends(get_auth_config),
) -> RefreshTokenResponse:
    """Refresh access token using refresh token."""
    service = AuthService(repository, security, config)

    # Get client info
    ip_address = req.client.host if req.client else "127.0.0.1"
    user_agent = req.headers.get("user-agent")

    try:
        return await service.refresh_access_token(request, ip_address, user_agent)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except Exception:
        await repository.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed",
        )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    request: Request,
    _: TokenPayload = Depends(get_current_token),  # Validate token
    repository: AuthRepository = Depends(get_auth_repository),
    security: SecurityUtils = Depends(get_security_utils),
    config: AuthConfig = Depends(get_auth_config),
) -> None:
    """Logout user by revoking tokens."""
    service = AuthService(repository, security, config)

    # Get access token from header
    auth_header = request.headers.get("authorization", "")
    access_token = (
        auth_header.replace("Bearer ", "")
        if auth_header.startswith("Bearer ")
        else None
    )

    # Get refresh token from request body if provided
    body = await request.body()
    refresh_token = None
    if body:
        import json

        try:
            data = json.loads(body)
            refresh_token = data.get("refresh_token")
        except (json.JSONDecodeError, AttributeError):
            pass

    if access_token:
        try:
            await service.logout_user(access_token, refresh_token)
        except Exception:
            await repository.rollback()
            # Don't raise error on logout failure, just log it
            pass


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: UserResponse = Depends(get_current_active_user),
) -> UserResponse:
    """Get current user information."""
    return current_user


@router.get("/verify-token", response_model=dict)
async def verify_token(
    token_payload: TokenPayload = Depends(get_current_token),
) -> dict:
    """Verify if token is valid."""
    return {
        "valid": True,
        "user_id": token_payload.sub,
        "token_type": token_payload.token_type,
        "session_id": token_payload.session_id,
    }


@router.get("/test-api-key", response_model=dict)
async def test_api_key(_: None = Depends(require_api_key)) -> dict:
    """Test endpoint that requires API key authentication."""
    return {
        "message": "API key authentication successful",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
