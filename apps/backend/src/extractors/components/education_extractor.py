"""Education section extractor."""

from typing import List, Optional
from pydantic import BaseModel, Field

from src.models.base import BaseLLMSchema
from src.models.llm.education import EducationLLMSchema
from src.extractors.base_extractor import BaseExtractor


class EducationListSchema(BaseLLMSchema):
    """Schema for extracting multiple education entries."""

    education_entries: List[EducationLLMSchema] = Field(
        default_factory=list,
        description="List of all education experiences found in the resume",
    )

    extraction_notes: Optional[str] = Field(
        None, description="Any notes about the extraction (e.g., ambiguous entries)"
    )


class EducationExtractor(BaseExtractor[EducationListSchema]):
    """Extractor for education section of resumes."""

    def get_extraction_prompt(self) -> str:
        """Get the prompt for education extraction."""
        return """Extract ALL education experiences from this resume including:
        
        1. University/College degrees (Bachelor's, Master's, PhD, etc.)
        2. High school education if mentioned
        3. Professional certifications and courses
        4. Online courses and bootcamps
        5. Exchange programs and study abroad
        6. Any other formal education or training
        
        For each education entry, extract:
        - Institution name
        - Degree type and level
        - Field of study/major
        - Specialization or focus area
        - Start and end dates
        - GPA if mentioned (with scale)
        - Any honors, awards, or notable achievements
        
        Be thorough and include every educational experience mentioned."""

    def get_response_model(self):
        """Get the response model for education extraction."""
        return EducationListSchema
