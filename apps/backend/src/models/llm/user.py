"""LLM schema for user/person data extraction."""

from typing import Optional, List
from pydantic import Field, EmailStr, HttpUrl
from src.models.base import BaseLLMSchema
from .education import EducationLLMSchema
from .work import WorkExperienceLLMSchema
from .project import ProjectLLMSchema
from .skill import SkillLLMSchema


class UserLLMSchema(BaseLLMSchema):
    """Schema for user/person information extracted by LLM.

    All fields are optional to allow partial extraction from resumes or profiles.
    """

    first_name: Optional[str] = Field(
        None,
        description="Person's first name",
        json_schema_extra={
            "llm_context": "Extract the person's first name or given name",
            "examples": ["John", "Jane", "Michael"],
        },
    )

    last_name: Optional[str] = Field(
        None,
        description="Person's last name",
        json_schema_extra={
            "llm_context": "Extract the person's last name or family name",
            "examples": ["Doe", "Smith", "Johnson"],
        },
    )

    full_name: Optional[str] = Field(
        None,
        description="Person's full name",
        json_schema_extra={
            "llm_context": "Extract the complete name if first/last not clearly separated",
            "examples": ["John Doe", "Jane Smith Jr.", "Dr. Michael Johnson"],
        },
    )

    name_prefix: Optional[str] = Field(
        None,
        description="Name prefix or title",
        json_schema_extra={
            "llm_context": "Extract any title or prefix (Dr., Mr., Ms., Prof., etc.)",
            "examples": ["Dr.", "Mr.", "Ms.", "Prof."],
        },
    )

    name_suffix: Optional[str] = Field(
        None,
        description="Name suffix",
        json_schema_extra={
            "llm_context": "Extract any suffix (Jr., Sr., III, PhD, etc.)",
            "examples": ["Jr.", "Sr.", "III", "PhD", "MD"],
        },
    )

    email: Optional[EmailStr] = Field(
        None,
        description="Email address",
        json_schema_extra={
            "llm_context": "Extract the email address",
            "examples": ["john.doe@email.com", "contact@example.com"],
        },
    )

    phone: Optional[str] = Field(
        None,
        description="Phone number",
        json_schema_extra={
            "llm_context": "Extract the phone number in any format",
            "examples": ["+1-555-123-4567", "(555) 123-4567", "555.123.4567"],
        },
    )

    location: Optional[str] = Field(
        None,
        description="Current location",
        json_schema_extra={
            "llm_context": "Extract the person's location (city, state, country)",
            "examples": ["San Francisco, CA", "New York, NY, USA", "London, UK"],
        },
    )

    linkedin_url: Optional[HttpUrl] = Field(
        None,
        description="LinkedIn profile URL",
        json_schema_extra={
            "llm_context": "Extract LinkedIn profile URL",
            "examples": [
                "https://linkedin.com/in/johndoe",
                "https://www.linkedin.com/in/jane-smith",
            ],
        },
    )

    github_url: Optional[HttpUrl] = Field(
        None,
        description="GitHub profile URL",
        json_schema_extra={
            "llm_context": "Extract GitHub profile URL",
            "examples": [
                "https://github.com/johndoe",
                "https://www.github.com/janesmith",
            ],
        },
    )

    portfolio_url: Optional[HttpUrl] = Field(
        None,
        description="Personal website or portfolio URL",
        json_schema_extra={
            "llm_context": "Extract personal website, portfolio, or blog URL",
            "examples": ["https://johndoe.com", "https://portfolio.example.com"],
        },
    )

    summary: Optional[str] = Field(
        None,
        description="Professional summary or objective",
        json_schema_extra={
            "llm_context": "Extract the professional summary, objective, or about section",
            "examples": [
                "Experienced software engineer with 5+ years in full-stack development",
                "Data scientist passionate about machine learning and AI",
            ],
        },
    )

    educations: List[EducationLLMSchema] = Field(
        default_factory=list,
        description="Educational background",
        json_schema_extra={"llm_context": "Extract all educational experiences"},
    )

    work_experiences: List[WorkExperienceLLMSchema] = Field(
        default_factory=list,
        description="Work experience history",
        json_schema_extra={
            "llm_context": "Extract all work experiences and employment history"
        },
    )

    projects: List[ProjectLLMSchema] = Field(
        default_factory=list,
        description="Personal or professional projects",
        json_schema_extra={"llm_context": "Extract all projects mentioned"},
    )

    skills: List[SkillLLMSchema] = Field(
        default_factory=list,
        description="Skills and competencies",
        json_schema_extra={
            "llm_context": "Extract all skills, technologies, and competencies mentioned"
        },
    )
