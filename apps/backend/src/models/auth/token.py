"""Token schemas."""
from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime


class TokenPayload(BaseModel):
    """JWT token payload schema."""
    
    sub: str = Field(..., description="Subject (user ID)")
    exp: datetime = Field(..., description="Expiration time")
    iat: datetime = Field(..., description="Issued at time")
    jti: Optional[str] = Field(None, description="JWT ID for blacklisting")
    token_type: str = Field(..., description="Token type (access/refresh)")
    session_id: Optional[str] = Field(None, description="Session ID for refresh tokens")


class RefreshTokenRequest(BaseModel):
    """Refresh token request schema."""
    
    refresh_token: str = Field(..., description="JWT refresh token")


class RefreshTokenResponse(BaseModel):
    """Refresh token response schema."""
    
    access_token: str = Field(..., description="New JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Access token expiration in seconds")