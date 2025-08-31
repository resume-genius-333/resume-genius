"""LLM schema for education data extraction."""

from typing import Optional
from pydantic import Field
from src.models.base import BaseLLMSchema
from src.models.db.enums import DegreeType


class EducationLLMSchema(BaseLLMSchema):
    """Schema for education information extracted by LLM.

    All fields are optional to allow partial extraction.
    """

    institution_name: Optional[str] = Field(
        None,
        description="Name of the educational institution",
        json_schema_extra={
            "llm_context": "Extract the school, university, or institution name",
            "examples": ["MIT", "Stanford University", "Harvard Business School"],
        },
    )

    degree: Optional[DegreeType] = Field(
        None,
        description="Type of degree obtained or pursued",
        json_schema_extra={
            "llm_context": "Identify the degree level (bachelor, master, doctorate, etc.)",
            "examples": ["bachelor", "master", "doctorate"],
        },
    )

    field_of_study: Optional[str] = Field(
        None,
        description="Major or field of study",
        json_schema_extra={
            "llm_context": "Extract the major, concentration, or field of study",
            "examples": [
                "Computer Science",
                "Business Administration",
                "Electrical Engineering",
            ],
        },
    )

    focus_area: Optional[str] = Field(
        None,
        description="Specialization or focus area within the field",
        json_schema_extra={
            "llm_context": "Extract any specialization, minor, or focus area if mentioned",
            "examples": ["Machine Learning", "Finance", "Data Science"],
        },
    )

    start_date: Optional[str] = Field(
        None,
        description="Start date of education (any format)",
        json_schema_extra={
            "llm_context": "Extract when the education started (year or month/year)",
            "examples": ["2018", "September 2018", "2018-09"],
        },
    )

    end_date: Optional[str] = Field(
        None,
        description="End date of education (any format)",
        json_schema_extra={
            "llm_context": "Extract when the education ended or expected to end",
            "examples": ["2022", "May 2022", "2022-05", "Present", "Expected 2024"],
        },
    )

    gpa: Optional[float] = Field(
        None,
        ge=0.0,
        description="Grade Point Average",
        json_schema_extra={
            "llm_context": "Extract the GPA if mentioned",
            "examples": [3.8, 3.95, 4.0],
        },
    )

    max_gpa: Optional[float] = Field(
        None,
        ge=0.0,
        description="Maximum possible GPA (scale)",
        json_schema_extra={
            "llm_context": "Extract the GPA scale if mentioned (usually 4.0 or 5.0)",
            "examples": [4.0, 5.0],
        },
    )
