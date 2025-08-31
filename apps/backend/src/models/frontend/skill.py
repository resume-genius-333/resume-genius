"""Frontend schema for skill validation."""

from typing import Optional
from pydantic import Field
from src.models.base import BaseFrontendSchema
from src.models.db.enums import SkillCategory, ProficiencyLevel


class SkillFrontendSchema(BaseFrontendSchema):
    """Schema for skill information with frontend validation requirements.

    Required fields: skill_name, skill_category
    """

    skill_name: str = Field(
        ...,
        min_length=1,
        description="Name of the skill",
        json_schema_extra={
            "ui_label": "Skill Name",
            "ui_hint": "Enter the skill or technology name",
            "ui_required": True,
        },
    )

    skill_category: SkillCategory = Field(
        ...,
        description="Category of the skill",
        json_schema_extra={
            "ui_label": "Skill Category",
            "ui_hint": "Select the category that best describes this skill",
            "ui_required": True,
        },
    )

    proficiency_level: Optional[ProficiencyLevel] = Field(
        None,
        description="Proficiency level of the skill",
        json_schema_extra={
            "ui_label": "Proficiency Level",
            "ui_hint": "Optional: Select your proficiency level",
            "ui_required": False,
        },
    )
