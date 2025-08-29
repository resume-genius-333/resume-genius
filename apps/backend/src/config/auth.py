"""Authentication configuration."""
from typing import Optional
from pydantic import BaseModel, Field


class AuthConfig(BaseModel):
    """Authentication configuration settings."""
    
    # JWT Settings
    jwt_secret_key: str = Field(..., description="Secret key for JWT signing")
    jwt_algorithm: str = Field(default="HS256", description="JWT signing algorithm")
    access_token_expire_minutes: int = Field(default=30, description="Access token expiration in minutes")
    refresh_token_expire_days: int = Field(default=7, description="Refresh token expiration in days")
    
    # Password Policy
    password_min_length: int = Field(default=8, description="Minimum password length")
    password_require_uppercase: bool = Field(default=True, description="Require uppercase letter")
    password_require_lowercase: bool = Field(default=True, description="Require lowercase letter")
    password_require_digit: bool = Field(default=True, description="Require digit")
    password_require_special: bool = Field(default=True, description="Require special character")
    
    # Security Settings
    max_login_attempts: int = Field(default=5, description="Maximum login attempts before lockout")
    lockout_duration_minutes: int = Field(default=30, description="Account lockout duration in minutes")
    
    # Token Settings
    password_reset_token_expire_hours: int = Field(default=24, description="Password reset token expiration")
    email_verification_token_expire_hours: int = Field(default=48, description="Email verification token expiration")
    
    class Config:
        env_prefix = "AUTH_"