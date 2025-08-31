"""Registration schemas."""
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, field_validator
import re


class UserRegisterRequest(BaseModel):
    """User registration request schema."""
    
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=8, description="User password")
    first_name: str = Field(..., min_length=1, max_length=100, description="First name")
    last_name: Optional[str] = Field(None, max_length=100, description="Last name")
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", v):
            raise ValueError("Password must contain at least one special character")
        return v
    
    @field_validator('first_name', 'last_name')
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        """Validate name fields."""
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError("Name cannot be empty")
            if not re.match(r"^[a-zA-Z\s\-']+$", v):
                raise ValueError("Name can only contain letters, spaces, hyphens, and apostrophes")
        return v


class UserRegisterResponse(BaseModel):
    """User registration response schema."""
    
    id: str = Field(..., description="User ID")
    email: str = Field(..., description="User email")
    first_name: str = Field(..., description="First name")
    last_name: Optional[str] = Field(None, description="Last name")
    full_name: Optional[str] = Field(None, description="Full name")
    is_active: bool = Field(..., description="Account active status")
    email_verified: bool = Field(..., description="Email verification status")
    created_at: str = Field(..., description="Account creation timestamp")