"""Work experience section extractor."""

from typing import List, Optional
from pydantic import BaseModel, Field

from src.schemas.base import BaseLLMSchema
from src.schemas.llm.work import WorkExperienceLLMSchema
from src.extractors.base_extractor import BaseExtractor


class WorkListSchema(BaseLLMSchema):
    """Schema for extracting multiple work experience entries."""
    
    work_entries: List[WorkExperienceLLMSchema] = Field(
        default_factory=list,
        description="List of all work experiences found in the resume"
    )
    
    extraction_notes: Optional[str] = Field(
        None,
        description="Any notes about the extraction"
    )


class WorkExtractor(BaseExtractor[WorkListSchema]):
    """Extractor for work experience section of resumes."""
    
    def get_extraction_prompt(self) -> str:
        """Get the prompt for work experience extraction."""
        return """Extract ALL work experiences from this resume including:
        
        1. Full-time positions
        2. Part-time positions
        3. Internships
        4. Contract/Freelance work
        5. Volunteer experiences
        6. Teaching or research assistantships
        7. Self-employment or entrepreneurial ventures
        
        For each work experience, extract:
        - Company/Organization name
        - Position/Job title
        - Employment type (full-time, part-time, internship, etc.)
        - Location (city, state, country, or "Remote")
        - Start and end dates
        - ALL responsibilities and achievements as separate items
        - Skills and technologies used in each responsibility
        
        IMPORTANT: Extract every single responsibility, achievement, and bullet point 
        mentioned for each position. Each should be a separate entry with associated 
        skills/technologies if mentioned.
        
        Be comprehensive and include all work-related experiences."""
    
    def get_response_model(self):
        """Get the response model for work experience extraction."""
        return WorkListSchema