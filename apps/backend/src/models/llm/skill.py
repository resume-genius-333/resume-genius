"""LLM schema for skill data extraction."""

from typing import Optional
from pydantic import Field
from src.models.base import BaseLLMSchema
from src.models.db.enums import SkillCategory, ProficiencyLevel


class SkillLLMSchema(BaseLLMSchema):
    """Schema for skill information extracted by LLM.

    All fields are optional to allow partial extraction.
    """

    skill_name: Optional[str] = Field(
        None,
        description="Name of the skill",
        json_schema_extra={
            "llm_context": "Extract the specific skill, technology, tool, or competency",
            "examples": ["Python", "Project Management", "AWS", "React", "Leadership"],
        },
    )

    skill_category: Optional[SkillCategory] = Field(
        None,
        description="Category of the skill",
        json_schema_extra={
            "llm_context": "Categorize the skill (programming_language, framework, tool, etc.)",
            "examples": ["programming_language", "framework", "cloud", "soft_skill"],
        },
    )

    proficiency_level: Optional[ProficiencyLevel] = Field(
        None,
        description="Proficiency level of the skill",
        json_schema_extra={
            "llm_context": "Estimate proficiency level if indicated (beginner to expert)",
            "examples": ["beginner", "intermediate", "advanced", "expert"],
        },
    )
