"""Base schema classes for the application."""
from typing import Any, Dict
from pydantic import BaseModel, ConfigDict


class BaseLLMSchema(BaseModel):
    """Base schema for LLM extraction with all optional fields."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        use_enum_values=False,
        validate_assignment=True,
        arbitrary_types_allowed=False,
        json_schema_extra={
            "description": "Base schema for LLM data extraction"
        }
    )

    def to_db_model(self, **kwargs) -> Any:
        """Convert schema to database model.

        Args:
            **kwargs: Additional arguments like user_id, session, etc.

        Returns:
            Database model instance
        """
        raise NotImplementedError("Subclasses must implement to_db_model")

    @classmethod
    def from_db_model(cls, db_model: Any) -> "BaseLLMSchema":
        """Create schema from database model.

        Args:
            db_model: Database model instance

        Returns:
            Schema instance
        """
        raise NotImplementedError("Subclasses must implement from_db_model")


class BaseFrontendSchema(BaseModel):
    """Base schema for frontend validation with required fields."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        use_enum_values=False,
        validate_assignment=True,
        arbitrary_types_allowed=False,
        json_schema_extra={
            "description": "Base schema for frontend validation"
        }
    )

    @classmethod
    def get_required_fields(cls) -> Dict[str, Dict[str, Any]]:
        """Get required fields with their metadata.

        Returns:
            Dictionary of required field names to their metadata
        """
        required_fields = {}
        for field_name, field_info in cls.model_fields.items():
            if field_info.is_required():
                required_fields[field_name] = {
                    "type": str(field_info.annotation),
                    "description": field_info.description or "",
                    "json_schema_extra": field_info.json_schema_extra or {}
                }
        return required_fields

    @classmethod
    def validate_against_llm(cls, llm_data: BaseLLMSchema) -> Dict[str, Any]:
        """Validate LLM data against frontend requirements.

        Args:
            llm_data: Data extracted by LLM

        Returns:
            Validation result with missing fields and status
        """
        missing_fields = []
        field_errors: dict[str, str] = {}

        for field_name, field_info in cls.model_fields.items():
            if field_info.is_required():
                value = getattr(llm_data, field_name, None)
                if value is None or (isinstance(value, str) and value.strip() == ""):
                    missing_fields.append({
                        "field_name": field_name,
                        "field_type": str(field_info.annotation),
                        "description": field_info.description or "",
                        "metadata": field_info.json_schema_extra or {}
                    })

        # Calculate completeness
        total_fields = len(cls.model_fields)
        filled_fields = sum(
            1 for field_name in cls.model_fields
            if getattr(llm_data, field_name, None) is not None
        )
        completeness = (filled_fields / total_fields * 100) if total_fields > 0 else 0

        return {
            "validation_status": "complete" if not missing_fields else "incomplete",
            "missing_required_fields": missing_fields,
            "field_errors": field_errors,
            "completeness_percentage": round(completeness, 2)
        }

