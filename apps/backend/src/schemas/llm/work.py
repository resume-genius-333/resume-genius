"""LLM schema for work experience data extraction."""
from typing import Optional, List
from pydantic import Field
from src.schemas.base import BaseLLMSchema
from src.models.enums import EmploymentType


class WorkResponsibilityLLMSchema(BaseLLMSchema):
    """Schema for work responsibility/achievement extracted by LLM."""
    
    description: Optional[str] = Field(
        None,
        description="Description of the responsibility or achievement",
        json_schema_extra={
            "llm_context": "Extract the specific responsibility, achievement, or task performed",
            "examples": [
                "Led a team of 5 engineers to develop a new microservices architecture",
                "Increased sales by 25% through strategic marketing campaigns",
                "Implemented CI/CD pipeline reducing deployment time by 40%"
            ]
        }
    )
    
    skills_demonstrated: List[str] = Field(
        default_factory=list,
        description="Skills demonstrated in this responsibility",
        json_schema_extra={
            "llm_context": "Identify skills or technologies used in this responsibility",
            "examples": [["Python", "Docker", "AWS"], ["Leadership", "Project Management"]]
        }
    )


class WorkExperienceLLMSchema(BaseLLMSchema):
    """Schema for work experience information extracted by LLM.
    
    All fields are optional to allow partial extraction.
    """
    
    company_name: Optional[str] = Field(
        None,
        description="Name of the company or organization",
        json_schema_extra={
            "llm_context": "Extract the employer's name or organization",
            "examples": ["Google", "Microsoft", "Startup Inc.", "Self-employed"]
        }
    )
    
    position_title: Optional[str] = Field(
        None,
        description="Job title or position",
        json_schema_extra={
            "llm_context": "Extract the job title or role",
            "examples": ["Software Engineer", "Product Manager", "Data Scientist", "CEO"]
        }
    )
    
    employment_type: Optional[EmploymentType] = Field(
        None,
        description="Type of employment",
        json_schema_extra={
            "llm_context": "Identify the employment type (full-time, part-time, contract, etc.)",
            "examples": ["full_time", "part_time", "contract", "internship"]
        }
    )
    
    location: Optional[str] = Field(
        None,
        description="Work location",
        json_schema_extra={
            "llm_context": "Extract the work location (city, state, country, or 'Remote')",
            "examples": ["San Francisco, CA", "New York, NY", "Remote", "London, UK"]
        }
    )
    
    start_date: Optional[str] = Field(
        None,
        description="Start date of employment (any format)",
        json_schema_extra={
            "llm_context": "Extract when the employment started (year or month/year)",
            "examples": ["2020", "January 2020", "2020-01"]
        }
    )
    
    end_date: Optional[str] = Field(
        None,
        description="End date of employment (any format)",
        json_schema_extra={
            "llm_context": "Extract when the employment ended or if current",
            "examples": ["2023", "December 2023", "2023-12", "Present", "Current"]
        }
    )
    
    responsibilities: List[WorkResponsibilityLLMSchema] = Field(
        default_factory=list,
        description="List of responsibilities and achievements",
        json_schema_extra={
            "llm_context": "Extract all responsibilities, achievements, and key tasks"
        }
    )