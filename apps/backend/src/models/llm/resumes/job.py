from pydantic import Field
from src.models.base import BaseLLMSchema


class JobLLMSchema(BaseLLMSchema):
    company_name: str
    position_title: str
    job_description: str = Field(
        description="Job description formatted properly in Github Flavored Markdown."
    )
