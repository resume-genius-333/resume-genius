from src.models.base import BaseLLMSchema


class JobLLMSchema(BaseLLMSchema):
    company_name: str
    position_title: str
    job_description: str
