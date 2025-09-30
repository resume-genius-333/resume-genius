"""API models for user profile management endpoints."""

from typing import Optional, List
from pydantic import BaseModel, Field

from src.models.db.profile.education import ProfileEducationSchema
from src.models.db.enums import DegreeType, EmploymentType
from src.models.db.profile.project import ProfileProjectSchema
from src.models.db.profile.work import ProfileWorkExperienceSchema


# Education Models
class EducationCreateRequest(BaseModel):
    """Request model for creating education entry."""

    institution_name: str = Field()
    degree: DegreeType
    field_of_study: str = Field()
    focus_area: Optional[str] = Field(None)
    start_date: Optional[str] = Field(None)  # YYYY-MM format
    end_date: Optional[str] = Field(None)
    gpa: Optional[float] = Field(None)
    max_gpa: Optional[float] = Field(None)


class EducationUpdateRequest(BaseModel):
    """Request model for updating education entry."""

    institution_name: Optional[str] = Field(None)
    degree: Optional[DegreeType] = None
    field_of_study: Optional[str] = Field(None)
    focus_area: Optional[str] = Field(None)
    start_date: Optional[str] = Field(None)
    end_date: Optional[str] = Field(None)
    gpa: Optional[float] = Field(None)
    max_gpa: Optional[float] = Field(None)


# Work Experience Models
class WorkResponsibilityRequest(BaseModel):
    """Request model for work responsibility."""

    description: str = Field()


class WorkExperienceCreateRequest(BaseModel):
    """Request model for creating work experience."""

    company_name: str = Field()
    position_title: str = Field()
    employment_type: EmploymentType
    location: Optional[str] = Field(None)
    start_date: Optional[str] = Field(None)
    end_date: Optional[str] = Field(None)
    responsibilities: Optional[List[str]] = Field(default_factory=list)


class WorkExperienceUpdateRequest(BaseModel):
    """Request model for updating work experience."""

    company_name: Optional[str] = Field(None)
    position_title: Optional[str] = Field(None)
    employment_type: Optional[EmploymentType] = None
    location: Optional[str] = Field(None)
    start_date: Optional[str] = Field(None)
    end_date: Optional[str] = Field(None)


# Project Models
class ProjectTaskRequest(BaseModel):
    """Request model for project task."""

    description: str = Field()


class ProjectCreateRequest(BaseModel):
    """Request model for creating project."""

    project_name: str = Field()
    description: Optional[str] = Field(None)
    start_date: Optional[str] = Field(None)
    end_date: Optional[str] = Field(None)
    project_url: Optional[str] = None
    repository_url: Optional[str] = None
    tasks: Optional[List[str]] = Field(default_factory=list)


class ProjectUpdateRequest(BaseModel):
    """Request model for updating project."""

    project_name: Optional[str] = Field(None)
    description: Optional[str] = Field(None)
    start_date: Optional[str] = Field(None)
    end_date: Optional[str] = Field(None)
    project_url: Optional[str] = None
    repository_url: Optional[str] = None


# List Response Models
class EducationListResponse(BaseModel):
    """Response model for list of educations."""

    educations: List[ProfileEducationSchema]
    total: int


class WorkExperienceListResponse(BaseModel):
    """Response model for list of work experiences."""

    work_experiences: List[ProfileWorkExperienceSchema]
    total: int


class ProjectListResponse(BaseModel):
    """Response model for list of projects."""

    projects: List[ProfileProjectSchema]
    total: int

class CreateProfileResumeUploadUrlRequest(BaseModel):
    sha256_checksum: str
    md5_checksum: str

class CreateProfileResumeUploadUrlResponse(BaseModel):
    fileId: str
    uploadUrl: str

class StartProfileResumeExtractionRequest(BaseModel):
    fileId: str

class StartProfileResumeExtractionResponse(BaseModel):
    fileId: str