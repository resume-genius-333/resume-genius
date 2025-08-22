"""Skills section extractor."""

from typing import List, Optional
from pydantic import BaseModel, Field

from src.schemas.llm.skill import SkillLLMSchema
from src.extractors.base_extractor import BaseExtractor


class SkillListSchema(BaseModel):
    """Schema for extracting multiple skill entries."""
    
    skill_entries: List[SkillLLMSchema] = Field(
        default_factory=list,
        description="List of all skills found in the resume"
    )
    
    extraction_notes: Optional[str] = Field(
        None,
        description="Any notes about the extraction"
    )


class SkillExtractor(BaseExtractor[SkillListSchema]):
    """Extractor for skills section of resumes."""
    
    def get_extraction_prompt(self) -> str:
        """Get the prompt for skill extraction."""
        return """Extract ALL skills from this resume including:
        
        1. Programming languages (Python, Java, JavaScript, etc.)
        2. Frameworks and libraries (React, Django, Spring, etc.)
        3. Databases (MySQL, PostgreSQL, MongoDB, etc.)
        4. Cloud platforms (AWS, Azure, GCP, etc.)
        5. Development tools (Git, Docker, Kubernetes, etc.)
        6. Soft skills (Leadership, Communication, Problem-solving, etc.)
        7. Domain knowledge (Machine Learning, Finance, Healthcare, etc.)
        8. Languages (English, Spanish, Mandarin, etc.)
        9. Certifications and qualifications
        10. Any other technical or non-technical skills
        
        For each skill, extract:
        - Skill name (exact as mentioned)
        - Category (programming_language, framework, database, tool, cloud, soft_skill, domain, other)
        - Proficiency level if indicated (beginner, intermediate, advanced, expert)
        
        IMPORTANT: 
        - Extract skills from ALL sections of the resume, not just the skills section
        - Include skills mentioned in work experience, projects, and education
        - Each skill should be a separate entry
        - If a skill appears multiple times, extract it only once
        - Preserve the exact name as mentioned (e.g., "React.js" not just "React")
        
        Be comprehensive and extract every skill, technology, and competency mentioned."""
    
    def get_response_model(self):
        """Get the response model for skill extraction."""
        return SkillListSchema