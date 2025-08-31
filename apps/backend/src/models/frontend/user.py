"""Frontend schema for user validation."""

from typing import Optional, List
from pydantic import Field, EmailStr, HttpUrl
from src.models.base import BaseFrontendSchema
from .education import EducationFrontendSchema
from .work import WorkExperienceFrontendSchema
from .project import ProjectFrontendSchema
from .skill import SkillFrontendSchema


class UserFrontendSchema(BaseFrontendSchema):
    """Schema for user information with frontend validation requirements.

    Required fields: first_name, email
    """

    first_name: str = Field(
        ...,
        min_length=1,
        description="Person's first name",
        json_schema_extra={
            "ui_label": "First Name",
            "ui_hint": "Enter your first name",
            "ui_required": True,
        },
    )

    last_name: Optional[str] = Field(
        None,
        description="Person's last name",
        json_schema_extra={
            "ui_label": "Last Name",
            "ui_hint": "Enter your last name",
            "ui_required": False,
            "ui_recommended": True,
        },
    )

    full_name: Optional[str] = Field(
        None,
        description="Person's full name",
        json_schema_extra={
            "ui_label": "Full Name",
            "ui_hint": "Optional: Enter your full name if different from first + last",
            "ui_required": False,
        },
    )

    name_prefix: Optional[str] = Field(
        None,
        description="Name prefix or title",
        json_schema_extra={
            "ui_label": "Title/Prefix",
            "ui_hint": "Optional: Dr., Mr., Ms., Prof., etc.",
            "ui_required": False,
        },
    )

    name_suffix: Optional[str] = Field(
        None,
        description="Name suffix",
        json_schema_extra={
            "ui_label": "Suffix",
            "ui_hint": "Optional: Jr., Sr., III, PhD, etc.",
            "ui_required": False,
        },
    )

    email: EmailStr = Field(
        ...,
        description="Email address",
        json_schema_extra={
            "ui_label": "Email Address",
            "ui_hint": "Enter your email address",
            "ui_required": True,
            "ui_format": "email",
        },
    )

    phone: Optional[str] = Field(
        None,
        description="Phone number",
        json_schema_extra={
            "ui_label": "Phone Number",
            "ui_hint": "Enter your phone number",
            "ui_required": False,
            "ui_recommended": True,
            "ui_format": "phone",
        },
    )

    location: Optional[str] = Field(
        None,
        description="Current location",
        json_schema_extra={
            "ui_label": "Location",
            "ui_hint": "Enter your city and state/country",
            "ui_required": False,
            "ui_recommended": True,
        },
    )

    linkedin_url: Optional[HttpUrl] = Field(
        None,
        description="LinkedIn profile URL",
        json_schema_extra={
            "ui_label": "LinkedIn Profile",
            "ui_hint": "Optional: Link to your LinkedIn profile",
            "ui_required": False,
            "ui_format": "url",
        },
    )

    github_url: Optional[HttpUrl] = Field(
        None,
        description="GitHub profile URL",
        json_schema_extra={
            "ui_label": "GitHub Profile",
            "ui_hint": "Optional: Link to your GitHub profile",
            "ui_required": False,
            "ui_format": "url",
        },
    )

    portfolio_url: Optional[HttpUrl] = Field(
        None,
        description="Personal website or portfolio URL",
        json_schema_extra={
            "ui_label": "Portfolio/Website",
            "ui_hint": "Optional: Link to your personal website or portfolio",
            "ui_required": False,
            "ui_format": "url",
        },
    )

    summary: Optional[str] = Field(
        None,
        max_length=1000,
        description="Professional summary or objective",
        json_schema_extra={
            "ui_label": "Professional Summary",
            "ui_hint": "Optional: Brief summary of your professional background and goals",
            "ui_required": False,
            "ui_recommended": True,
            "ui_format": "textarea",
        },
    )

    educations: List[EducationFrontendSchema] = Field(
        default_factory=list,
        description="Educational background",
        json_schema_extra={
            "ui_label": "Education",
            "ui_hint": "Add your educational background",
            "ui_required": False,
            "ui_min_items": 0,
            "ui_recommended_items": 1,
        },
    )

    work_experiences: List[WorkExperienceFrontendSchema] = Field(
        default_factory=list,
        description="Work experience history",
        json_schema_extra={
            "ui_label": "Work Experience",
            "ui_hint": "Add your work experience",
            "ui_required": False,
            "ui_min_items": 0,
            "ui_recommended_items": 2,
        },
    )

    projects: List[ProjectFrontendSchema] = Field(
        default_factory=list,
        description="Personal or professional projects",
        json_schema_extra={
            "ui_label": "Projects",
            "ui_hint": "Add relevant projects",
            "ui_required": False,
            "ui_min_items": 0,
        },
    )

    skills: List[SkillFrontendSchema] = Field(
        default_factory=list,
        description="Skills and competencies",
        json_schema_extra={
            "ui_label": "Skills",
            "ui_hint": "Add your skills and competencies",
            "ui_required": False,
            "ui_min_items": 0,
            "ui_recommended_items": 5,
        },
    )
