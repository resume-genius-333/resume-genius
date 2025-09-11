"""Resume-related API request and response models."""

from typing import Optional, List, Any
import uuid
from datetime import datetime
from pydantic import BaseModel, Field


class PaginationParams(BaseModel):
    """Pagination parameters."""
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class PaginatedResponse(BaseModel):
    """Base model for paginated responses."""
    items: List[Any]
    total: int
    limit: int
    offset: int
    has_more: bool


class AIEnhanceRequest(BaseModel):
    """Request model for AI enhancement."""
    prompt: str = Field(..., min_length=1, max_length=2000)
    agent_mode: bool = Field(default=False)
    tone: Optional[str] = Field(default="professional")
    context: Optional[dict] = Field(default=None)


class ResumeVersionResponse(BaseModel):
    """Response model for resume version."""
    version: uuid.UUID
    user_id: uuid.UUID
    job_id: uuid.UUID
    parent_version: Optional[uuid.UUID]
    metadata_id: uuid.UUID
    pinned_education_ids: List[uuid.UUID]
    pinned_experience_ids: List[uuid.UUID]
    pinned_project_ids: List[uuid.UUID]
    pinned_skill_ids: List[uuid.UUID]
    created_at: datetime
    updated_at: datetime


class ResumeMetadataRequest(BaseModel):
    """Request model for updating resume metadata."""
    user_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    portfolio_website: Optional[str] = None
    custom_styles: Optional[dict] = None


class ResumeMetadataResponse(BaseModel):
    """Response model for resume metadata."""
    id: uuid.UUID
    user_id: uuid.UUID
    job_id: uuid.UUID
    parent_id: Optional[uuid.UUID]
    user_name: str
    email: Optional[str]
    phone: Optional[str]
    location: Optional[str]
    linkedin_url: Optional[str]
    github_url: Optional[str]
    portfolio_website: Optional[str]
    custom_styles: Optional[dict]
    created_at: datetime
    updated_at: datetime


class ResumeEducationRequest(BaseModel):
    """Request model for updating resume education."""
    institution_name: Optional[str] = None
    degree: Optional[str] = None
    field_of_study: Optional[str] = None
    focus_area: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    gpa: Optional[float] = None
    max_gpa: Optional[float] = None
    city: Optional[str] = None
    country: Optional[str] = None


class ResumeEducationResponse(BaseModel):
    """Response model for resume education."""
    id: uuid.UUID
    user_id: uuid.UUID
    job_id: uuid.UUID
    parent_id: Optional[uuid.UUID]
    institution_name: str
    degree: str
    field_of_study: str
    focus_area: Optional[str]
    start_date: Optional[str]
    end_date: Optional[str]
    gpa: Optional[float]
    max_gpa: Optional[float]
    city: Optional[str]
    country: Optional[str]
    created_at: datetime
    updated_at: datetime


class ResumeWorkExperienceRequest(BaseModel):
    """Request model for updating resume work experience."""
    job_title: Optional[str] = None
    company_name: Optional[str] = None
    employment_type: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None
    achievements: Optional[List[str]] = None


class ResumeWorkExperienceResponse(BaseModel):
    """Response model for resume work experience."""
    id: uuid.UUID
    user_id: uuid.UUID
    job_id: uuid.UUID
    parent_id: Optional[uuid.UUID]
    job_title: str
    company_name: str
    employment_type: Optional[str]
    start_date: Optional[str]
    end_date: Optional[str]
    location: Optional[str]
    description: Optional[str]
    achievements: Optional[List[str]]
    created_at: datetime
    updated_at: datetime


class ResumeProjectRequest(BaseModel):
    """Request model for updating resume project."""
    project_name: Optional[str] = None
    role: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None
    technologies: Optional[List[str]] = None
    url: Optional[str] = None


class ResumeProjectResponse(BaseModel):
    """Response model for resume project."""
    id: uuid.UUID
    user_id: uuid.UUID
    job_id: uuid.UUID
    parent_id: Optional[uuid.UUID]
    project_name: str
    role: Optional[str]
    start_date: Optional[str]
    end_date: Optional[str]
    location: Optional[str]
    description: Optional[str]
    technologies: Optional[List[str]]
    url: Optional[str]
    created_at: datetime
    updated_at: datetime


class ResumeSkillRequest(BaseModel):
    """Request model for updating resume skill."""
    skill_name: Optional[str] = None
    skill_category: Optional[str] = None
    proficiency_level: Optional[str] = None
    years_of_experience: Optional[int] = None


class ResumeSkillResponse(BaseModel):
    """Response model for resume skill."""
    id: uuid.UUID
    user_id: uuid.UUID
    job_id: uuid.UUID
    parent_id: Optional[uuid.UUID]
    skill_name: str
    skill_category: Optional[str]
    proficiency_level: Optional[str]
    years_of_experience: Optional[int]
    created_at: datetime
    updated_at: datetime


class FullResumeResponse(BaseModel):
    """Response model for full resume with all sections."""
    version: ResumeVersionResponse
    metadata: Optional[ResumeMetadataResponse]
    educations: List[ResumeEducationResponse]
    work_experiences: List[ResumeWorkExperienceResponse]
    projects: List[ResumeProjectResponse]
    skills: List[ResumeSkillResponse]


class CreateResumeVersionRequest(BaseModel):
    """Request model for creating a new resume version."""
    job_id: uuid.UUID
    parent_version: Optional[uuid.UUID] = None
    metadata_id: Optional[uuid.UUID] = None
    pinned_education_ids: Optional[List[uuid.UUID]] = Field(default_factory=list)
    pinned_experience_ids: Optional[List[uuid.UUID]] = Field(default_factory=list)
    pinned_project_ids: Optional[List[uuid.UUID]] = Field(default_factory=list)
    pinned_skill_ids: Optional[List[uuid.UUID]] = Field(default_factory=list)


class UpdateResumeVersionRequest(BaseModel):
    """Request model for updating resume version pins."""
    metadata_id: Optional[uuid.UUID] = None
    pinned_education_ids: Optional[List[uuid.UUID]] = None
    pinned_experience_ids: Optional[List[uuid.UUID]] = None
    pinned_project_ids: Optional[List[uuid.UUID]] = None
    pinned_skill_ids: Optional[List[uuid.UUID]] = None