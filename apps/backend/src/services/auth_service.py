"""Authentication service for business logic."""
from typing import Optional, Tuple
from datetime import datetime, timezone
from src.repositories.auth_repository import AuthRepository
from src.core.security import SecurityUtils
from src.config.auth import AuthConfig
from src.schemas.auth import (
    UserRegisterRequest,
    UserRegisterResponse,
    UserLoginRequest,
    UserLoginResponse,
    UserResponse,
    RefreshTokenRequest,
    RefreshTokenResponse
)
from src.models import ProviderType


class AuthService:
    """Service for authentication business logic."""
    
    def __init__(
        self,
        repository: AuthRepository,
        security: SecurityUtils,
        config: AuthConfig
    ):
        """Initialize auth service with dependencies."""
        self.repository = repository
        self.security = security
        self.config = config
    
    async def register_user(
        self,
        request: UserRegisterRequest,
        ip_address: str,
        user_agent: Optional[str] = None
    ) -> UserRegisterResponse:
        """Register a new user."""
        # Check if user already exists
        existing_user = await self.repository.get_user_by_email(request.email)
        if existing_user:
            raise ValueError("User with this email already exists")
        
        # Create user
        user = await self.repository.create_user(
            email=request.email,
            first_name=request.first_name,
            last_name=request.last_name
        )
        
        # Hash password and create auth provider
        password_hash = self.security.hash_password(request.password)
        await self.repository.create_auth_provider(
            user_id=user.id,
            provider_type=ProviderType.PASSWORD,
            password_hash=password_hash,
            provider_email=request.email
        )
        
        # Commit transaction
        await self.repository.commit()
        
        # Return response
        return UserRegisterResponse(
            id=str(user.id),
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            full_name=user.full_name,
            is_active=user.is_active,
            email_verified=user.email_verified,
            created_at=user.created_at.isoformat()
        )
    
    async def login_user(
        self,
        request: UserLoginRequest,
        ip_address: str,
        user_agent: Optional[str] = None
    ) -> UserLoginResponse:
        """Authenticate user and create session."""
        # Get user
        user = await self.repository.get_user_by_email(request.email)
        if not user:
            raise ValueError("Invalid email or password")
        
        # Check if user is active
        if not user.is_active:
            raise ValueError("Account is deactivated")
        
        # Get auth provider
        auth_provider = await self.repository.get_auth_provider(
            user_id=user.id,
            provider_type=ProviderType.PASSWORD
        )
        if not auth_provider:
            raise ValueError("Invalid email or password")
        
        # Check if account is locked
        if auth_provider.locked_until:
            if auth_provider.locked_until > datetime.now(timezone.utc):
                raise ValueError("Account is temporarily locked due to too many failed attempts")
            else:
                # Unlock if lockout period has passed
                auth_provider.locked_until = None
                auth_provider.failed_attempts = 0
        
        # Verify password
        if not self.security.verify_password(request.password, auth_provider.password_hash):
            await self.repository.update_login_attempt(auth_provider, success=False)
            await self.repository.commit()
            raise ValueError("Invalid email or password")
        
        # Reset failed attempts on successful login
        await self.repository.update_login_attempt(auth_provider, success=True)
        
        # Generate session ID
        session_id = self.security.generate_session_id()
        
        # Create tokens
        access_token = self.security.create_access_token(str(user.id), session_id)
        refresh_token = self.security.create_refresh_token(str(user.id), session_id)
        
        # Hash refresh token for storage
        refresh_token_hash = self.security.hash_token(refresh_token)
        
        # Store refresh token
        refresh_token_model = await self.repository.create_refresh_token(
            user_id=user.id,
            token_hash=refresh_token_hash,
            ip_address=ip_address,
            user_agent=user_agent,
            expires_days=self.config.refresh_token_expire_days if not request.remember_me else 30
        )
        
        # Create user session
        await self.repository.create_user_session(
            user_id=user.id,
            refresh_token_id=refresh_token_model.id,
            session_id=session_id,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        # Update last login
        await self.repository.update_user_last_login(user.id)
        
        # Commit transaction
        await self.repository.commit()
        
        # Return response
        return UserLoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=self.config.access_token_expire_minutes * 60
        )
    
    async def refresh_access_token(
        self,
        request: RefreshTokenRequest,
        ip_address: str,
        user_agent: Optional[str] = None
    ) -> RefreshTokenResponse:
        """Refresh access token using refresh token."""
        # Decode refresh token
        token_payload = self.security.decode_token(request.refresh_token)
        if not token_payload or token_payload.token_type != "refresh":
            raise ValueError("Invalid refresh token")
        
        # Check if token is blacklisted
        if await self.repository.is_token_blacklisted(token_payload.jti):
            raise ValueError("Token has been revoked")
        
        # Hash token and get from database
        token_hash = self.security.hash_token(request.refresh_token)
        refresh_token_model = await self.repository.get_refresh_token(token_hash)
        if not refresh_token_model:
            raise ValueError("Invalid refresh token")
        
        # Get user
        user = await self.repository.get_user_by_id(token_payload.sub)
        if not user or not user.is_active:
            raise ValueError("User not found or inactive")
        
        # Update refresh token last used
        refresh_token_model.last_used_at = datetime.now(timezone.utc)
        
        # Update session activity
        if token_payload.session_id:
            await self.repository.update_session_activity(token_payload.session_id)
        
        # Create new access token
        access_token = self.security.create_access_token(
            str(user.id),
            token_payload.session_id
        )
        
        # Commit transaction
        await self.repository.commit()
        
        # Return response
        return RefreshTokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=self.config.access_token_expire_minutes * 60
        )
    
    async def logout_user(
        self,
        access_token: str,
        refresh_token: Optional[str] = None
    ) -> None:
        """Logout user by revoking tokens and ending session."""
        # Decode access token
        access_payload = self.security.decode_token(access_token)
        if access_payload:
            # Blacklist access token
            await self.repository.blacklist_token(
                jti=access_payload.jti,
                user_id=access_payload.sub,
                expires_at=access_payload.exp,
                reason="User logout"
            )
            
            # End session
            if access_payload.session_id:
                await self.repository.end_user_session(access_payload.session_id)
        
        # Revoke refresh token if provided
        if refresh_token:
            refresh_payload = self.security.decode_token(refresh_token)
            if refresh_payload:
                # Blacklist refresh token
                await self.repository.blacklist_token(
                    jti=refresh_payload.jti,
                    user_id=refresh_payload.sub,
                    expires_at=refresh_payload.exp,
                    reason="User logout"
                )
                
                # Revoke refresh token in database
                token_hash = self.security.hash_token(refresh_token)
                await self.repository.revoke_refresh_token(token_hash)
        
        # Commit transaction
        await self.repository.commit()
    
    async def get_current_user(self, user_id: str) -> UserResponse:
        """Get current user information."""
        user = await self.repository.get_user_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        
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
            updated_at=user.updated_at
        )