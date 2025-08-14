"""Frontend schema for project validation."""
from typing import Optional, List
from pydantic import Field, HttpUrl
from src.schemas.base import BaseFrontendSchema


class ProjectTaskFrontendSchema(BaseFrontendSchema):
    """Schema for project task with frontend validation requirements.
    
    Required fields: description
    """
    
    description: str = Field(
        ...,
        min_length=1,
        description="Description of the task or feature",
        json_schema_extra={
            "ui_label": "Task/Feature",
            "ui_hint": "Describe a key task or feature you implemented",
            "ui_required": True
        }
    )
    
    skills_demonstrated: List[str] = Field(
        default_factory=list,
        description="Skills demonstrated in this task",
        json_schema_extra={
            "ui_label": "Skills Used",
            "ui_hint": "Optional: List skills used for this task",
            "ui_required": False
        }
    )


class ProjectFrontendSchema(BaseFrontendSchema):
    """Schema for project with frontend validation requirements.
    
    Required fields: project_name
    """
    
    project_name: str = Field(
        ...,
        min_length=1,
        description="Name of the project",
        json_schema_extra={
            "ui_label": "Project Name",
            "ui_hint": "Enter the name of your project",
            "ui_required": True
        }
    )
    
    description: Optional[str] = Field(
        None,
        description="Brief description of the project",
        json_schema_extra={
            "ui_label": "Project Description",
            "ui_hint": "Optional: Briefly describe what the project does",
            "ui_required": False
        }
    )
    
    start_date: Optional[str] = Field(
        None,
        description="Start date of the project",
        json_schema_extra={
            "ui_label": "Start Date",
            "ui_hint": "When did you start this project?",
            "ui_required": False,
            "ui_format": "date"
        }
    )
    
    end_date: Optional[str] = Field(
        None,
        description="End date of the project",
        json_schema_extra={
            "ui_label": "End Date",
            "ui_hint": "When did this project end? (Leave blank if ongoing)",
            "ui_required": False,
            "ui_format": "date"
        }
    )
    
    project_url: Optional[HttpUrl] = Field(
        None,
        description="URL to the live project or demo",
        json_schema_extra={
            "ui_label": "Project URL",
            "ui_hint": "Optional: Link to the live project or demo",
            "ui_required": False,
            "ui_format": "url"
        }
    )
    
    repository_url: Optional[HttpUrl] = Field(
        None,
        description="URL to the project repository",
        json_schema_extra={
            "ui_label": "Repository URL",
            "ui_hint": "Optional: Link to GitHub or other repository",
            "ui_required": False,
            "ui_format": "url"
        }
    )
    
    tasks: List[ProjectTaskFrontendSchema] = Field(
        default_factory=list,
        description="List of tasks and features implemented",
        json_schema_extra={
            "ui_label": "Tasks & Features",
            "ui_hint": "Add key tasks and features you implemented",
            "ui_required": False,
            "ui_min_items": 0,
            "ui_recommended_items": 3
        }
    )
    
    technologies_used: List[str] = Field(
        default_factory=list,
        description="Technologies and tools used in the project",
        json_schema_extra={
            "ui_label": "Technologies Used",
            "ui_hint": "List the technologies, frameworks, and tools used",
            "ui_required": False
        }
    )