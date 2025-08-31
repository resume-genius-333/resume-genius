"""Response schemas for validation and extraction results."""
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field
from enum import Enum


class ValidationStatus(str, Enum):
    """Status of validation."""
    COMPLETE = "complete"
    INCOMPLETE = "incomplete"
    INVALID = "invalid"
    EMPTY = "empty"


class FieldInfo(BaseModel):
    """Information about a field."""

    field_name: str = Field(
        ...,
        description="Name of the field"
    )

    field_type: str = Field(
        ...,
        description="Type of the field"
    )

    description: str = Field(
        "",
        description="Description of the field"
    )

    ui_label: Optional[str] = Field(
        None,
        description="Label to display in UI"
    )

    ui_hint: Optional[str] = Field(
        None,
        description="Hint text for UI"
    )

    ui_required: bool = Field(
        False,
        description="Whether field is required in UI"
    )

    ui_recommended: bool = Field(
        False,
        description="Whether field is recommended in UI"
    )

    error_message: Optional[str] = Field(
        None,
        description="Error message if validation failed"
    )


class ValidationResponse(BaseModel):
    """Response containing validation results for extracted data."""

    data: Dict[str, Any] = Field(
        ...,
        description="The extracted data (may be incomplete)"
    )

    validation_status: ValidationStatus = Field(
        ...,
        description="Overall validation status"
    )

    missing_required_fields: List[FieldInfo] = Field(
        default_factory=list,
        description="List of required fields that are missing"
    )

    missing_recommended_fields: List[FieldInfo] = Field(
        default_factory=list,
        description="List of recommended fields that are missing"
    )

    field_errors: Dict[str, str] = Field(
        default_factory=dict,
        description="Validation errors per field"
    )

    completeness_percentage: float = Field(
        0.0,
        ge=0.0,
        le=100.0,
        description="Percentage of fields that are filled"
    )

    required_completeness_percentage: float = Field(
        0.0,
        ge=0.0,
        le=100.0,
        description="Percentage of required fields that are filled"
    )

    frontend_schema: Dict[str, Any] = Field(
        default_factory=dict,
        description="JSON schema of frontend requirements"
    )

    extraction_metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Metadata about the extraction process"
    )


class ExtractionResponse(BaseModel):
    """Response for LLM extraction results."""

    extracted_data: Dict[str, Any] = Field(
        ...,
        description="Data extracted by LLM"
    )

    validation: ValidationResponse = Field(
        ...,
        description="Validation results against frontend requirements"
    )

    source_type: Literal["resume", "text", "profile", "manual"] = Field(
        "text",
        description="Type of source data"
    )

    extraction_confidence: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Confidence score of extraction (0-1)"
    )

    extraction_model: Optional[str] = Field(
        None,
        description="Model used for extraction"
    )

    extraction_timestamp: Optional[str] = Field(
        None,
        description="Timestamp of extraction"
    )

    suggestions: List[str] = Field(
        default_factory=list,
        description="Suggestions for improving the data"
    )

    warnings: List[str] = Field(
        default_factory=list,
        description="Warnings about the extracted data"
    )

