"""Frontend schemas for validation with required fields."""
from .user import UserFrontendSchema
from .education import EducationFrontendSchema
from .work import WorkExperienceFrontendSchema, WorkResponsibilityFrontendSchema
from .project import ProjectFrontendSchema, ProjectTaskFrontendSchema
from .skill import SkillFrontendSchema

__all__ = [
    "UserFrontendSchema",
    "EducationFrontendSchema",
    "WorkExperienceFrontendSchema",
    "WorkResponsibilityFrontendSchema",
    "ProjectFrontendSchema",
    "ProjectTaskFrontendSchema",
    "SkillFrontendSchema",
]