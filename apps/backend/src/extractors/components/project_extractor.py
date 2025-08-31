"""Project section extractor."""

from typing import List, Optional
from pydantic import BaseModel, Field

from src.models.base import BaseLLMSchema
from src.models.llm.project import ProjectLLMSchema
from src.extractors.base_extractor import BaseExtractor


class ProjectListSchema(BaseLLMSchema):
    """Schema for extracting multiple project entries."""

    project_entries: List[ProjectLLMSchema] = Field(
        default_factory=list, description="List of all projects found in the resume"
    )

    extraction_notes: Optional[str] = Field(
        None, description="Any notes about the extraction"
    )


class ProjectExtractor(BaseExtractor[ProjectListSchema]):
    """Extractor for projects section of resumes."""

    def get_extraction_prompt(self) -> str:
        """Get the prompt for project extraction."""
        return """Extract ALL projects from this resume including:
        
        1. Personal projects
        2. Academic projects
        3. Open source contributions
        4. Hackathon projects
        5. Professional/work projects (if listed separately)
        6. Research projects
        7. Any other significant technical or non-technical projects
        
        For each project, extract:
        - Project name/title
        - Brief description of what the project does
        - Start and end dates (or if ongoing)
        - Project URL (if deployed or available online)
        - Repository URL (GitHub, GitLab, etc.)
        - ALL specific tasks, features, or contributions as separate items
        - Technologies, frameworks, and tools used
        - Skills demonstrated in each task
        
        IMPORTANT: Extract every task, feature, and contribution mentioned for each 
        project as separate entries. Include all technical details and technologies used.
        
        Be thorough and capture all project-related information."""

    def get_response_model(self):
        """Get the response model for project extraction."""
        return ProjectListSchema
