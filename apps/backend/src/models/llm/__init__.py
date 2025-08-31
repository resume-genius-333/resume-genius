"""LLM schemas for data extraction with all optional fields."""
from .user import UserLLMSchema
from .education import EducationLLMSchema
from .work import WorkExperienceLLMSchema, WorkResponsibilityLLMSchema
from .project import ProjectLLMSchema, ProjectTaskLLMSchema
from .skill import SkillLLMSchema

__all__ = [
    "UserLLMSchema",
    "EducationLLMSchema",
    "WorkExperienceLLMSchema",
    "WorkResponsibilityLLMSchema",
    "ProjectLLMSchema",
    "ProjectTaskLLMSchema",
    "SkillLLMSchema",
]