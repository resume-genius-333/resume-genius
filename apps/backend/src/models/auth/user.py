"""User schemas for authentication."""
from typing import Optional
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime


class UserResponse(BaseModel):
    """User response schema (without sensitive data)."""
    
    id: str = Field(..., description="User ID")
    email: EmailStr = Field(..., description="User email")
    first_name: str = Field(..., description="First name")
    last_name: Optional[str] = Field(None, description="Last name")
    full_name: Optional[str] = Field(None, description="Full name")
    name_prefix: Optional[str] = Field(None, description="Name prefix")
    name_suffix: Optional[str] = Field(None, description="Name suffix")
    phone: Optional[str] = Field(None, description="Phone number")
    location: Optional[str] = Field(None, description="Location")
    avatar_url: Optional[str] = Field(None, description="Avatar URL")
    linkedin_url: Optional[str] = Field(None, description="LinkedIn URL")
    github_url: Optional[str] = Field(None, description="GitHub URL")
    portfolio_url: Optional[str] = Field(None, description="Portfolio URL")
    is_active: bool = Field(..., description="Account active status")
    email_verified: bool = Field(..., description="Email verification status")
    email_verified_at: Optional[datetime] = Field(None, description="Email verification timestamp")
    last_login_at: Optional[datetime] = Field(None, description="Last login timestamp")
    created_at: datetime = Field(..., description="Account creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    class Config:
        from_attributes = True