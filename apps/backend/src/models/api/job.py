"""Job-related API request and response models."""

from typing import Optional
import uuid
from pydantic import BaseModel


class CreateJobRequest(BaseModel):
    """Request model for creating a job."""
    job_description: str
    job_url: Optional[str] = None


class CreateJobResponse(BaseModel):
    """Response model for job creation."""
    job_id: uuid.UUID
    sse_url: str


class SelectRelevantInfoRequest(BaseModel):
    """Request model for selecting relevant resume information."""
    # Add fields as needed when implementing the feature
    pass


class SelectRelevantInfoResponse(BaseModel):
    """Response model for selected relevant information."""
    status: str
    message: str
    # Add more fields as needed


class RefineResumeRequest(BaseModel):
    """Request model for refining resume."""
    # Add fields as needed when implementing the feature
    pass


class RefineResumeResponse(BaseModel):
    """Response model for resume refinement."""
    status: str
    message: str
    # Add more fields as needed