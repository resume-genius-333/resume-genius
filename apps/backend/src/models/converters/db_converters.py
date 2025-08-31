"""Converters between Pydantic schemas and database models."""

from typing import Any, Dict, List, Optional, Type
from datetime import datetime
import uuid

from sqlalchemy.orm import Session

from src.models.db.user import User
from src.models.db.education import Education
from src.models.db.work import WorkExperience, WorkResponsibility
from src.models.db.project import Project, ProjectTask
from src.models.db.enums import DegreeType, EmploymentType

from src.models.llm import (
    UserLLMSchema,
    EducationLLMSchema,
    WorkExperienceLLMSchema,
    ProjectLLMSchema,
    SkillLLMSchema,
)
from src.models.frontend import (
    UserFrontendSchema,
)
from src.models.response import ValidationResponse, FieldInfo, ValidationStatus


class SchemaConverter:
    """Converter for transforming between different schema types."""

    @staticmethod
    def llm_to_db_user(
        llm_data: UserLLMSchema, _session: Optional[Session] = None
    ) -> User:
        """Convert LLM User schema to database User model.

        Args:
            llm_data: LLM extracted user data
            _session: Optional database session for relationship handling

        Returns:
            User database model instance
        """
        # TODO: Add summary field to User database model to store llm_data.summary
        user = User(
            id=uuid.uuid4(),
            first_name=llm_data.first_name or "",
            full_name=llm_data.full_name,
            last_name=llm_data.last_name,
            name_prefix=llm_data.name_prefix,
            name_suffix=llm_data.name_suffix,
            email=str(llm_data.email)
            if llm_data.email
            else f"placeholder_{uuid.uuid4().hex[:8]}@example.com",
            phone=llm_data.phone,
            location=llm_data.location,
            linkedin_url=str(llm_data.linkedin_url) if llm_data.linkedin_url else None,
            github_url=str(llm_data.github_url) if llm_data.github_url else None,
            portfolio_url=str(llm_data.portfolio_url)
            if llm_data.portfolio_url
            else None,
        )
        return user

    @staticmethod
    def llm_to_db_education(
        llm_data: EducationLLMSchema, user_id: uuid.UUID
    ) -> Education:
        """Convert LLM Education schema to database Education model.

        Args:
            llm_data: LLM extracted education data
            user_id: ID of the user this education belongs to

        Returns:
            Education database model instance
        """
        return Education(
            id=uuid.uuid4(),
            user_id=user_id,
            institution_name=llm_data.institution_name or "",
            degree=llm_data.degree or DegreeType.OTHER,
            field_of_study=llm_data.field_of_study or "",
            focus_area=llm_data.focus_area,
            start_date=llm_data.start_date,
            end_date=llm_data.end_date,
            gpa=llm_data.gpa,
            max_gpa=llm_data.max_gpa,
        )

    @staticmethod
    def llm_to_db_work_experience(
        llm_data: WorkExperienceLLMSchema,
        user_id: uuid.UUID,
        _session: Optional[Session] = None,
    ) -> WorkExperience:
        """Convert LLM WorkExperience schema to database WorkExperience model.

        Args:
            llm_data: LLM extracted work experience data
            user_id: ID of the user this work experience belongs to
            _session: Optional database session for relationship handling

        Returns:
            WorkExperience database model instance
        """
        work_exp = WorkExperience(
            id=uuid.uuid4(),
            user_id=user_id,
            company_name=llm_data.company_name or "",
            position_title=llm_data.position_title or "",
            employment_type=llm_data.employment_type or EmploymentType.OTHER,
            location=llm_data.location,
            start_date=llm_data.start_date,
            end_date=llm_data.end_date,
        )

        # Convert responsibilities
        if llm_data.responsibilities:
            work_exp.responsibilities = [
                WorkResponsibility(
                    id=uuid.uuid4(),
                    work_id=work_exp.id,
                    user_id=user_id,
                    description=resp.description or "",
                )
                for resp in llm_data.responsibilities
            ]

        return work_exp

    @staticmethod
    def llm_to_db_project(
        llm_data: ProjectLLMSchema,
        user_id: uuid.UUID,
        _session: Optional[Session] = None,
    ) -> Project:
        """Convert LLM Project schema to database Project model.

        Args:
            llm_data: LLM extracted project data
            user_id: ID of the user this project belongs to
            _session: Optional database session for relationship handling

        Returns:
            Project database model instance
        """
        project = Project(
            id=uuid.uuid4(),
            user_id=user_id,
            project_name=llm_data.project_name or "",
            description=llm_data.description,
            start_date=llm_data.start_date,
            end_date=llm_data.end_date,
            project_url=str(llm_data.project_url) if llm_data.project_url else None,
            repository_url=str(llm_data.repository_url)
            if llm_data.repository_url
            else None,
        )

        # Convert tasks
        if llm_data.tasks:
            project.tasks = [
                ProjectTask(
                    id=uuid.uuid4(),
                    project_id=project.id,
                    user_id=user_id,
                    description=task.description or "",
                )
                for task in llm_data.tasks
            ]

        return project

    @staticmethod
    def db_to_llm_user(db_user: User) -> UserLLMSchema:
        """Convert database User model to LLM schema.

        Args:
            db_user: Database user model

        Returns:
            UserLLMSchema instance
        """
        from pydantic import HttpUrl

        return UserLLMSchema(
            first_name=db_user.first_name,
            last_name=db_user.last_name,
            full_name=db_user.full_name,
            name_prefix=db_user.name_prefix,
            name_suffix=db_user.name_suffix,
            email=db_user.email,
            phone=db_user.phone,
            location=db_user.location,
            linkedin_url=HttpUrl(db_user.linkedin_url)
            if db_user.linkedin_url
            else None,
            github_url=HttpUrl(db_user.github_url) if db_user.github_url else None,
            portfolio_url=HttpUrl(db_user.portfolio_url)
            if db_user.portfolio_url
            else None,
            summary=None,  # Database doesn't have summary field yet
            educations=[
                EducationLLMSchema(
                    institution_name=edu.institution_name,
                    degree=edu.degree,
                    field_of_study=edu.field_of_study,
                    focus_area=edu.focus_area,
                    start_date=edu.start_date,
                    end_date=edu.end_date,
                    gpa=edu.gpa,
                    max_gpa=edu.max_gpa,
                )
                for edu in db_user.educations
            ]
            if hasattr(db_user, "educations")
            else [],
            work_experiences=[
                WorkExperienceLLMSchema(
                    company_name=work.company_name,
                    position_title=work.position_title,
                    employment_type=work.employment_type,
                    location=work.location,
                    start_date=work.start_date,
                    end_date=work.end_date,
                )
                for work in db_user.work_experiences
            ]
            if hasattr(db_user, "work_experiences")
            else [],
            projects=[
                ProjectLLMSchema(
                    project_name=proj.project_name,
                    description=proj.description,
                    start_date=proj.start_date,
                    end_date=proj.end_date,
                    project_url=HttpUrl(proj.project_url) if proj.project_url else None,
                    repository_url=HttpUrl(proj.repository_url)
                    if proj.repository_url
                    else None,
                )
                for proj in db_user.projects
            ]
            if hasattr(db_user, "projects")
            else [],
            skills=[
                SkillLLMSchema(
                    skill_name=user_skill.skill.skill_name,
                    skill_category=user_skill.skill.skill_category,
                    proficiency_level=user_skill.proficiency_level,
                )
                for user_skill in db_user.user_skills
            ]
            if hasattr(db_user, "user_skills") and db_user.user_skills
            else [],
        )


class ValidationService:
    """Service for validating LLM data against frontend requirements."""

    @staticmethod
    def _get_json_schema_extra(field_info: Any) -> Dict[str, Any]:
        """Extract json_schema_extra from field_info, handling callable case.

        Args:
            field_info: Pydantic FieldInfo object

        Returns:
            Dictionary of json schema extra data
        """
        json_extra = field_info.json_schema_extra
        if json_extra is None:
            return {}
        elif callable(json_extra):
            # If it's a function, call it with empty dict
            result = json_extra({})
            # Ensure we return a dict
            if isinstance(result, dict):
                return result
            else:
                return {}
        elif isinstance(json_extra, dict):
            return json_extra
        else:
            # Fallback for any other type
            return {}

    @staticmethod
    def validate_user(
        llm_data: UserLLMSchema,
        frontend_schema: Type[UserFrontendSchema] = UserFrontendSchema,
    ) -> ValidationResponse:
        """Validate LLM user data against frontend requirements.

        Args:
            llm_data: Data extracted by LLM
            frontend_schema: Frontend schema class to validate against

        Returns:
            ValidationResponse with validation results
        """
        missing_required: List[FieldInfo] = []
        missing_recommended: List[FieldInfo] = []
        field_errors: Dict[str, str] = {}

        # Check each field in frontend schema
        for field_name, field_info in frontend_schema.model_fields.items():
            value = getattr(llm_data, field_name, None)

            # Get field metadata using helper function
            json_extra = ValidationService._get_json_schema_extra(field_info)
            ui_required: bool = bool(json_extra.get("ui_required", False))
            ui_recommended: bool = bool(json_extra.get("ui_recommended", False))

            # Create field info
            field_data = FieldInfo(
                field_name=field_name,
                field_type=str(field_info.annotation),
                description=field_info.description or "",
                ui_label=str(json_extra.get("ui_label", field_name)),
                ui_hint=str(json_extra.get("ui_hint", "")),
                ui_required=ui_required,
                ui_recommended=ui_recommended,
                error_message=None,  # Will be populated if there's a validation error
            )

            # Check if required field is missing
            if field_info.is_required() or ui_required:
                if value is None or (isinstance(value, str) and not value.strip()):
                    missing_required.append(field_data)
            # Check if recommended field is missing
            elif ui_recommended:
                if value is None or (isinstance(value, str) and not value.strip()):
                    missing_recommended.append(field_data)

        # Calculate completeness
        total_fields = len(frontend_schema.model_fields)
        filled_fields = sum(
            1
            for field_name in frontend_schema.model_fields
            if getattr(llm_data, field_name, None) is not None
        )
        completeness = (filled_fields / total_fields * 100) if total_fields > 0 else 0

        # Calculate required completeness
        required_fields = sum(
            1
            for field_info in frontend_schema.model_fields.values()
            if field_info.is_required()
            or ValidationService._get_json_schema_extra(field_info).get(
                "ui_required", False
            )
        )
        filled_required = required_fields - len(missing_required)
        required_completeness = (
            (filled_required / required_fields * 100) if required_fields > 0 else 0
        )

        # Determine validation status
        if not llm_data.model_dump(exclude_none=True):
            status = ValidationStatus.EMPTY
        elif missing_required:
            status = ValidationStatus.INCOMPLETE
        elif field_errors:
            status = ValidationStatus.INVALID
        else:
            status = ValidationStatus.COMPLETE

        return ValidationResponse(
            data=llm_data.model_dump(exclude_none=True),
            validation_status=status,
            missing_required_fields=missing_required,
            missing_recommended_fields=missing_recommended,
            field_errors=field_errors,
            completeness_percentage=round(completeness, 2),
            required_completeness_percentage=round(required_completeness, 2),
            frontend_schema=frontend_schema.model_json_schema(),
            extraction_metadata={
                "timestamp": datetime.utcnow().isoformat(),
                "schema_version": "1.0.0",
            },
        )

    @staticmethod
    def merge_with_user_input(
        llm_data: UserLLMSchema, user_input: Dict[str, Any]
    ) -> UserLLMSchema:
        """Merge LLM extracted data with user input.

        Args:
            llm_data: Original LLM extracted data
            user_input: User provided updates

        Returns:
            Updated UserLLMSchema with merged data
        """
        # Create a copy and update with user input
        merged_data = llm_data.model_copy(update=user_input)
        return merged_data
