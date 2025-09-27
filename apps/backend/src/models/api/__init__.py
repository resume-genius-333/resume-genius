"""API request and response models."""

from .job import (
    CreateJobRequest,
    CreateJobResponse,
    SelectRelevantInfoRequest,
    SelectRelevantInfoResponse,
    RefineResumeRequest,
    RefineResumeResponse,
)
from .resume import (
    PaginationParams,
    PaginatedResponse,
    AIEnhanceRequest,
    ResumeMetadataRequest,
    ResumeEducationRequest,
    ResumeWorkExperienceRequest,
    ResumeProjectRequest,
    ResumeSkillRequest,
    FullResumeResponse,
    CreateResumeVersionRequest,
    UpdateResumeVersionRequest,
)

__all__ = [
    # Job models
    "CreateJobRequest",
    "CreateJobResponse",
    "SelectRelevantInfoRequest",
    "SelectRelevantInfoResponse",
    "RefineResumeRequest",
    "RefineResumeResponse",
    # Resume models
    "PaginationParams",
    "PaginatedResponse",
    "AIEnhanceRequest",
    "ResumeMetadataRequest",
    "ResumeEducationRequest",
    "ResumeWorkExperienceRequest",
    "ResumeProjectRequest",
    "ResumeSkillRequest",
    "FullResumeResponse",
    "CreateResumeVersionRequest",
    "UpdateResumeVersionRequest",
]
