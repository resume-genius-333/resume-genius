"""LLM schema for project data extraction."""

from typing import Optional, List
from pydantic import Field, HttpUrl
from src.models.base import BaseLLMSchema


class ProjectTaskLLMSchema(BaseLLMSchema):
    """Schema for project task/feature extracted by LLM."""

    description: Optional[str] = Field(
        None,
        description="Description of the task or feature",
        json_schema_extra={
            "llm_context": "Extract specific task, feature, or contribution in the project",
            "examples": [
                "Implemented user authentication using JWT",
                "Designed RESTful API endpoints",
                "Created responsive UI with React",
            ],
        },
    )

    skills_demonstrated: List[str] = Field(
        default_factory=list,
        description="Skills demonstrated in this task",
        json_schema_extra={
            "llm_context": "Identify skills or technologies used in this task",
            "examples": [
                ["React", "TypeScript", "CSS"],
                ["Python", "FastAPI", "PostgreSQL"],
            ],
        },
    )


class ProjectLLMSchema(BaseLLMSchema):
    """Schema for project information extracted by LLM.

    All fields are optional to allow partial extraction.
    """

    project_name: Optional[str] = Field(
        None,
        description="Name of the project",
        json_schema_extra={
            "llm_context": "Extract the project name or title",
            "examples": ["E-commerce Platform", "Task Management App", "ML Pipeline"],
        },
    )

    description: Optional[str] = Field(
        None,
        description="Brief description of the project",
        json_schema_extra={
            "llm_context": "Extract a summary or overview of what the project does",
            "examples": [
                "A web application for managing personal finances",
                "Machine learning model for predicting customer churn",
                "Open-source library for data visualization",
            ],
        },
    )

    start_date: Optional[str] = Field(
        None,
        description="Start date of the project (any format)",
        json_schema_extra={
            "llm_context": "Extract when the project started",
            "examples": ["2023", "January 2023", "2023-01"],
        },
    )

    end_date: Optional[str] = Field(
        None,
        description="End date of the project (any format)",
        json_schema_extra={
            "llm_context": "Extract when the project ended or if ongoing",
            "examples": ["2023", "June 2023", "2023-06", "Ongoing", "Present"],
        },
    )

    project_url: Optional[HttpUrl] = Field(
        None,
        description="URL to the live project or demo",
        json_schema_extra={
            "llm_context": "Extract URL to the deployed project, demo, or website",
            "examples": ["https://myproject.com", "https://demo.project.io"],
        },
    )

    repository_url: Optional[HttpUrl] = Field(
        None,
        description="URL to the project repository",
        json_schema_extra={
            "llm_context": "Extract URL to GitHub, GitLab, or other repository",
            "examples": [
                "https://github.com/user/project",
                "https://gitlab.com/user/project",
            ],
        },
    )

    tasks: List[ProjectTaskLLMSchema] = Field(
        default_factory=list,
        description="List of tasks and features implemented",
        json_schema_extra={
            "llm_context": "Extract specific tasks, features, or contributions made in the project"
        },
    )

    technologies_used: List[str] = Field(
        default_factory=list,
        description="Technologies and tools used in the project",
        json_schema_extra={
            "llm_context": "Extract all technologies, frameworks, and tools mentioned",
            "examples": [["Python", "Django", "PostgreSQL", "Docker", "AWS"]],
        },
    )
