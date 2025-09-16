"""Authentication router."""

import logging
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm

from dependency_injector.wiring import inject
from src.api.dependencies import (
    get_security_utils,
    get_auth_config,
    get_current_active_user,
    get_current_token,
    require_api_key,
)
from src.core.unit_of_work import UnitOfWorkFactory
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
from src.core.security import SecurityUtils
from src.config.auth import AuthConfig

# Configure logging
logger = logging.getLogger(__name__)


router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post(
    "/register",
    response_model=UserRegisterResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    request: UserRegisterRequest,
    req: Request,
    security: SecurityUtils = Depends(get_security_utils),
    config: AuthConfig = Depends(get_auth_config),
) -> UserRegisterResponse:
    """Register a new user."""
    # Get client info
    ip_address = req.client.host if req.client else "127.0.0.1"
    user_agent = req.headers.get("user-agent")

    async with UnitOfWorkFactory() as uow:
        service = AuthService(uow, security, config)
        try:
            result = await service.register_user(request, ip_address, user_agent)
            await uow.commit()
            return result
        except ValueError as e:
            await uow.rollback()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except Exception:
            await uow.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Registration failed",
            )


@router.post("/login", response_model=UserLoginResponse)
async def login(
    request: UserLoginRequest,
    req: Request,
    security: SecurityUtils = Depends(get_security_utils),
    config: AuthConfig = Depends(get_auth_config),
) -> UserLoginResponse:
    """Login user and create session."""
    # Get client info
    ip_address = req.client.host if req.client else "127.0.0.1"
    user_agent = req.headers.get("user-agent")

    async with UnitOfWorkFactory() as uow:
        service = AuthService(uow, security, config)
        try:
            result = await service.login_user(request, ip_address, user_agent)
            await uow.commit()
            return result
        except ValueError as e:
            await uow.rollback()
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
        except Exception:
            await uow.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Login failed"
            )


@router.post("/token")
async def token(
    req: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    security: SecurityUtils = Depends(get_security_utils),
    config: AuthConfig = Depends(get_auth_config),
):
    """
    OAuth2 compatible token endpoint for Swagger UI authentication.

    This endpoint accepts username (email) and password via form data
    and returns an access token in OAuth2 format.
    """
    logger.info(f"Token endpoint called with username: {form_data.username}")

    # Get client info
    ip_address = req.client.host if req and req.client else "127.0.0.1"
    user_agent = req.headers.get("user-agent") if req else None
    logger.debug(f"Client info - IP: {ip_address}, User-Agent: {user_agent}")

    # Create a UserLoginRequest from the OAuth2 form data
    login_request = UserLoginRequest(
        email=form_data.username,  # OAuth2 uses 'username' field
        password=form_data.password,
        remember_me=False,  # Default to False for OAuth2 flow
    )
    logger.debug(f"Login request created for email: {login_request.email}")

    async with UnitOfWorkFactory() as uow:
        service = AuthService(uow, security, config)
        logger.debug("Auth service initialized successfully")

        try:
            # Use the existing login service
            logger.info("Calling login_user service method")
            login_response = await service.login_user(
                login_request, ip_address, user_agent
            )
            await uow.commit()
            logger.info(f"Login successful for user: {login_request.email}")

            # Return OAuth2-compatible response
            return {
                "access_token": login_response.access_token,
                "token_type": "bearer",
                "expires_in": login_response.expires_in,
                # Optionally include refresh token if needed
                "refresh_token": login_response.refresh_token,
            }
        except ValueError as e:
            await uow.rollback()
            logger.warning(f"Authentication failed with ValueError: {str(e)}")
            # OAuth2 requires specific error format
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except Exception as e:
            await uow.rollback()
            logger.error(f"Unexpected error in token endpoint: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Authentication failed",
            )


@router.post("/refresh", response_model=RefreshTokenResponse)
async def refresh_token(
    request: RefreshTokenRequest,
    req: Request,
    security: SecurityUtils = Depends(get_security_utils),
    config: AuthConfig = Depends(get_auth_config),
) -> RefreshTokenResponse:
    """Refresh access token using refresh token."""
    # Get client info
    ip_address = req.client.host if req.client else "127.0.0.1"
    user_agent = req.headers.get("user-agent")

    async with UnitOfWorkFactory() as uow:
        service = AuthService(uow, security, config)
        try:
            result = await service.refresh_access_token(request, ip_address, user_agent)
            await uow.commit()
            return result
        except ValueError as e:
            await uow.rollback()
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
        except Exception:
            await uow.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Token refresh failed",
            )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    request: Request,
    _: TokenPayload = Depends(get_current_token),  # Validate token
    security: SecurityUtils = Depends(get_security_utils),
    config: AuthConfig = Depends(get_auth_config),
) -> None:
    """Logout user by revoking tokens."""
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
        async with UnitOfWorkFactory() as uow:
            service = AuthService(uow, security, config)
            try:
                await service.logout_user(access_token, refresh_token)
                await uow.commit()
            except Exception:
                await uow.rollback()
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
