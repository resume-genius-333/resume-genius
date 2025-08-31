"""Frontend schema for work experience validation."""

from typing import Optional, List
from pydantic import Field
from src.models.base import BaseFrontendSchema
from src.models.db.enums import EmploymentType


class WorkResponsibilityFrontendSchema(BaseFrontendSchema):
    """Schema for work responsibility with frontend validation requirements.

    Required fields: description
    """

    description: str = Field(
        ...,
        min_length=1,
        description="Description of the responsibility or achievement",
        json_schema_extra={
            "ui_label": "Responsibility/Achievement",
            "ui_hint": "Describe a key responsibility or achievement",
            "ui_required": True,
        },
    )

    skills_demonstrated: List[str] = Field(
        default_factory=list,
        description="Skills demonstrated in this responsibility",
        json_schema_extra={
            "ui_label": "Skills Used",
            "ui_hint": "Optional: List skills used for this responsibility",
            "ui_required": False,
        },
    )


class WorkExperienceFrontendSchema(BaseFrontendSchema):
    """Schema for work experience with frontend validation requirements.

    Required fields: company_name, position_title, employment_type
    """

    company_name: str = Field(
        ...,
        min_length=1,
        description="Name of the company or organization",
        json_schema_extra={
            "ui_label": "Company Name",
            "ui_hint": "Enter the name of your employer",
            "ui_required": True,
        },
    )

    position_title: str = Field(
        ...,
        min_length=1,
        description="Job title or position",
        json_schema_extra={
            "ui_label": "Position Title",
            "ui_hint": "Enter your job title",
            "ui_required": True,
        },
    )

    employment_type: EmploymentType = Field(
        ...,
        description="Type of employment",
        json_schema_extra={
            "ui_label": "Employment Type",
            "ui_hint": "Select the type of employment",
            "ui_required": True,
        },
    )

    location: Optional[str] = Field(
        None,
        description="Work location",
        json_schema_extra={
            "ui_label": "Location",
            "ui_hint": "Optional: Enter the work location or 'Remote'",
            "ui_required": False,
        },
    )

    start_date: Optional[str] = Field(
        None,
        description="Start date of employment",
        json_schema_extra={
            "ui_label": "Start Date",
            "ui_hint": "When did you start this position?",
            "ui_required": False,
            "ui_format": "date",
        },
    )

    end_date: Optional[str] = Field(
        None,
        description="End date of employment",
        json_schema_extra={
            "ui_label": "End Date",
            "ui_hint": "When did this position end? (Leave blank if current)",
            "ui_required": False,
            "ui_format": "date",
        },
    )

    responsibilities: List[WorkResponsibilityFrontendSchema] = Field(
        default_factory=list,
        description="List of responsibilities and achievements",
        json_schema_extra={
            "ui_label": "Responsibilities & Achievements",
            "ui_hint": "Add key responsibilities and achievements",
            "ui_required": False,
            "ui_min_items": 0,
            "ui_recommended_items": 3,
        },
    )
