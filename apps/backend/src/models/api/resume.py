"""Resume-related API request and response models."""

from typing import Optional, List, Any
import uuid
from pydantic import BaseModel, Field

from src.models.db.resumes.resume import ResumeSchema
from src.models.db.resumes.resume_education import ResumeEducationSchema
from src.models.db.resumes.resume_metadata import ResumeMetadataSchema
from src.models.db.resumes.resume_project import ResumeProjectSchema
from src.models.db.resumes.resume_skill import ResumeSkillSchema
from src.models.db.resumes.resume_work_experience import ResumeWorkExperienceSchema


class PaginationParams(BaseModel):
    """Pagination parameters."""

    limit: int = Field(default=20)
    offset: int = Field(default=0)


class PaginatedResponse(BaseModel):
    """Base model for paginated responses."""

    items: List[Any]
    total: int
    limit: int
    offset: int
    has_more: bool


class AIEnhanceRequest(BaseModel):
    """Request model for AI enhancement."""

    prompt: str = Field()
    agent_mode: bool = Field(default=False)
    tone: Optional[str] = Field(default="professional")
    context: Optional[dict] = Field(default=None)


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


class ResumeSkillRequest(BaseModel):
    """Request model for updating resume skill."""

    skill_name: Optional[str] = None
    skill_category: Optional[str] = None
    proficiency_level: Optional[str] = None
    years_of_experience: Optional[int] = None


class FullResumeResponse(BaseModel):
    """Response model for full resume with all sections."""

    version: ResumeSchema
    metadata: Optional[ResumeMetadataSchema]
    educations: List[ResumeEducationSchema]
    work_experiences: List[ResumeWorkExperienceSchema]
    projects: List[ResumeProjectSchema]
    skills: List[ResumeSkillSchema]


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
