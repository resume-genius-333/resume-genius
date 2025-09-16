"""API models for user profile management endpoints."""

from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field, HttpUrl

from src.models.db.enums import DegreeType, EmploymentType


# Education Models
class EducationCreateRequest(BaseModel):
    """Request model for creating education entry."""
    institution_name: str = Field(..., min_length=1, max_length=200)
    degree: DegreeType
    field_of_study: str = Field(..., min_length=1, max_length=200)
    focus_area: Optional[str] = Field(None, max_length=200)
    start_date: Optional[str] = Field(None, pattern=r"^\d{4}-\d{2}$")  # YYYY-MM format
    end_date: Optional[str] = Field(None, pattern=r"^\d{4}-\d{2}$")
    gpa: Optional[float] = Field(None, ge=0.0, le=5.0)
    max_gpa: Optional[float] = Field(None, ge=0.0, le=5.0)


class EducationUpdateRequest(BaseModel):
    """Request model for updating education entry."""
    institution_name: Optional[str] = Field(None, min_length=1, max_length=200)
    degree: Optional[DegreeType] = None
    field_of_study: Optional[str] = Field(None, min_length=1, max_length=200)
    focus_area: Optional[str] = Field(None, max_length=200)
    start_date: Optional[str] = Field(None, pattern=r"^\d{4}-\d{2}$")
    end_date: Optional[str] = Field(None, pattern=r"^\d{4}-\d{2}$")
    gpa: Optional[float] = Field(None, ge=0.0, le=5.0)
    max_gpa: Optional[float] = Field(None, ge=0.0, le=5.0)


class EducationResponse(BaseModel):
    """Response model for education entry."""
    id: UUID
    user_id: UUID
    institution_name: str
    degree: DegreeType
    field_of_study: str
    focus_area: Optional[str]
    start_date: Optional[str]
    end_date: Optional[str]
    gpa: Optional[float]
    max_gpa: Optional[float]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Work Experience Models
class WorkResponsibilityRequest(BaseModel):
    """Request model for work responsibility."""
    description: str = Field(..., min_length=1, max_length=500)


class WorkResponsibilityResponse(BaseModel):
    """Response model for work responsibility."""
    id: UUID
    work_id: UUID
    user_id: UUID
    description: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class WorkExperienceCreateRequest(BaseModel):
    """Request model for creating work experience."""
    company_name: str = Field(..., min_length=1, max_length=200)
    position_title: str = Field(..., min_length=1, max_length=200)
    employment_type: EmploymentType
    location: Optional[str] = Field(None, max_length=200)
    start_date: Optional[str] = Field(None, pattern=r"^\d{4}-\d{2}$")
    end_date: Optional[str] = Field(None, pattern=r"^\d{4}-\d{2}$")
    responsibilities: Optional[List[str]] = Field(default_factory=list)


class WorkExperienceUpdateRequest(BaseModel):
    """Request model for updating work experience."""
    company_name: Optional[str] = Field(None, min_length=1, max_length=200)
    position_title: Optional[str] = Field(None, min_length=1, max_length=200)
    employment_type: Optional[EmploymentType] = None
    location: Optional[str] = Field(None, max_length=200)
    start_date: Optional[str] = Field(None, pattern=r"^\d{4}-\d{2}$")
    end_date: Optional[str] = Field(None, pattern=r"^\d{4}-\d{2}$")


class WorkExperienceResponse(BaseModel):
    """Response model for work experience."""
    id: UUID
    user_id: UUID
    company_name: str
    position_title: str
    employment_type: EmploymentType
    location: Optional[str]
    start_date: Optional[str]
    end_date: Optional[str]
    responsibilities: List[WorkResponsibilityResponse]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Project Models
class ProjectTaskRequest(BaseModel):
    """Request model for project task."""
    description: str = Field(..., min_length=1, max_length=500)


class ProjectTaskResponse(BaseModel):
    """Response model for project task."""
    id: UUID
    project_id: UUID
    user_id: UUID
    description: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProjectCreateRequest(BaseModel):
    """Request model for creating project."""
    project_name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    start_date: Optional[str] = Field(None, pattern=r"^\d{4}-\d{2}$")
    end_date: Optional[str] = Field(None, pattern=r"^\d{4}-\d{2}$")
    project_url: Optional[HttpUrl] = None
    repository_url: Optional[HttpUrl] = None
    tasks: Optional[List[str]] = Field(default_factory=list)


class ProjectUpdateRequest(BaseModel):
    """Request model for updating project."""
    project_name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    start_date: Optional[str] = Field(None, pattern=r"^\d{4}-\d{2}$")
    end_date: Optional[str] = Field(None, pattern=r"^\d{4}-\d{2}$")
    project_url: Optional[HttpUrl] = None
    repository_url: Optional[HttpUrl] = None


class ProjectResponse(BaseModel):
    """Response model for project."""
    id: UUID
    user_id: UUID
    project_name: str
    description: Optional[str]
    start_date: Optional[str]
    end_date: Optional[str]
    project_url: Optional[str]
    repository_url: Optional[str]
    tasks: List[ProjectTaskResponse]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# List Response Models
class EducationListResponse(BaseModel):
    """Response model for list of educations."""
    educations: List[EducationResponse]
    total: int


class WorkExperienceListResponse(BaseModel):
    """Response model for list of work experiences."""
    work_experiences: List[WorkExperienceResponse]
    total: int


class ProjectListResponse(BaseModel):
    """Response model for list of projects."""
    projects: List[ProjectResponse]
    total: int