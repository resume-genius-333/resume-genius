"""Frontend schema for education validation."""
from typing import Optional
from pydantic import Field
from src.schemas.base import BaseFrontendSchema
from src.models.enums import DegreeType


class EducationFrontendSchema(BaseFrontendSchema):
    """Schema for education information with frontend validation requirements.
    
    Required fields: institution_name, degree, field_of_study
    """
    
    institution_name: str = Field(
        ...,
        min_length=1,
        description="Name of the educational institution",
        json_schema_extra={
            "ui_label": "Institution Name",
            "ui_hint": "Enter the name of your school or university",
            "ui_required": True
        }
    )
    
    degree: DegreeType = Field(
        ...,
        description="Type of degree obtained or pursued",
        json_schema_extra={
            "ui_label": "Degree Type",
            "ui_hint": "Select your degree level",
            "ui_required": True
        }
    )
    
    field_of_study: str = Field(
        ...,
        min_length=1,
        description="Major or field of study",
        json_schema_extra={
            "ui_label": "Field of Study",
            "ui_hint": "Enter your major or field of study",
            "ui_required": True
        }
    )
    
    focus_area: Optional[str] = Field(
        None,
        description="Specialization or focus area within the field",
        json_schema_extra={
            "ui_label": "Focus Area",
            "ui_hint": "Optional: Enter your specialization or minor",
            "ui_required": False
        }
    )
    
    start_date: Optional[str] = Field(
        None,
        description="Start date of education",
        json_schema_extra={
            "ui_label": "Start Date",
            "ui_hint": "When did you start this education?",
            "ui_required": False,
            "ui_format": "date"
        }
    )
    
    end_date: Optional[str] = Field(
        None,
        description="End date of education",
        json_schema_extra={
            "ui_label": "End Date",
            "ui_hint": "When did you complete or expect to complete?",
            "ui_required": False,
            "ui_format": "date"
        }
    )
    
    gpa: Optional[float] = Field(
        None,
        ge=0.0,
        le=5.0,
        description="Grade Point Average",
        json_schema_extra={
            "ui_label": "GPA",
            "ui_hint": "Optional: Enter your GPA",
            "ui_required": False,
            "ui_format": "number"
        }
    )
    
    max_gpa: Optional[float] = Field(
        None,
        ge=0.0,
        le=5.0,
        description="Maximum possible GPA (scale)",
        json_schema_extra={
            "ui_label": "GPA Scale",
            "ui_hint": "Optional: Enter the maximum GPA (e.g., 4.0 or 5.0)",
            "ui_required": False,
            "ui_format": "number"
        }
    )