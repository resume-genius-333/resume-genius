"""Main resume extractor that orchestrates all extraction components."""

from pathlib import Path
from typing import Dict, Any, Optional, List
import logging
import asyncio

from src.models.llm.user import UserLLMSchema
from src.extractors.base_extractor import BaseExtractor
from src.extractors.components import (
    EducationExtractor,
    WorkExtractor,
    ProjectExtractor,
    SkillExtractor,
    ContactExtractor,
)

logger = logging.getLogger(__name__)


class ResumeExtractor(BaseExtractor[UserLLMSchema]):
    """Main extractor for complete resume data."""

    def __init__(
        self,
        client=None,
        model: str = "gpt-5-nano",
        max_retries: int = 2,
        use_progressive_extraction: bool = True,
    ):
        """Initialize the resume extractor.

        Args:
            client: Instructor client instance.
            model: Model to use for extraction.
            max_retries: Maximum number of retries.
            use_progressive_extraction: Whether to extract sections progressively.
        """
        super().__init__(client, model, max_retries)
        self.use_progressive_extraction = use_progressive_extraction

        # Initialize component extractors
        self.education_extractor = EducationExtractor(client, model, max_retries)
        self.work_extractor = WorkExtractor(client, model, max_retries)
        self.project_extractor = ProjectExtractor(client, model, max_retries)
        self.skill_extractor = SkillExtractor(client, model, max_retries)
        self.contact_extractor = ContactExtractor(client, model, max_retries)

    def get_extraction_prompt(self) -> str:
        """Get the prompt for full resume extraction."""
        return """Extract all information from this resume including:
        1. Personal information (name, contact details, social links)
        2. Professional summary
        3. All education experiences
        4. All work experiences with responsibilities
        5. All projects with tasks and technologies
        6. All skills with categories and proficiency levels
        
        Be thorough and extract every detail available."""

    def get_response_model(self):
        """Get the response model for full resume extraction."""
        return UserLLMSchema

    async def extract_full_resume(
        self,
        pdf_path: Path,
        validate_sections: bool = True,
    ) -> Dict[str, Any]:
        """Extract complete resume with all sections.

        Args:
            pdf_path: Path to the PDF resume.
            validate_sections: Whether to validate each section.

        Returns:
            Dictionary with extracted data and metadata.
        """
        logger.info(f"Starting full resume extraction from {pdf_path.name}")

        if self.use_progressive_extraction:
            result = await self._progressive_extraction(pdf_path)
        else:
            result = await self._single_extraction(pdf_path)

        # Calculate section confidence scores
        confidence_scores = self._calculate_section_confidence(result["data"])
        result["confidence_scores"] = confidence_scores

        # Validate sections if requested
        if validate_sections:
            validation_results = self._validate_sections(result["data"])
            result["validation"] = validation_results

        logger.info(
            f"Resume extraction complete. Overall confidence: {confidence_scores['overall']:.2%}"
        )

        return result

    async def _single_extraction(self, pdf_path: Path) -> Dict[str, Any]:
        """Extract all resume data in a single call."""
        try:
            data = await self.extract_from_pdf(pdf_path)
            return {
                "success": True,
                "data": data,
                "method": "single_extraction",
            }
        except Exception as e:
            logger.error(f"Single extraction failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "method": "single_extraction",
            }

    async def _progressive_extraction(self, pdf_path: Path) -> Dict[str, Any]:
        """Extract resume data progressively by section."""
        logger.info("Using progressive extraction strategy")

        # First, extract basic structure
        base_data = await self.extract_from_pdf(pdf_path)

        # Then refine each section in parallel
        refinement_tasks = [
            self._refine_education(pdf_path, base_data),
            self._refine_work(pdf_path, base_data),
            self._refine_projects(pdf_path, base_data),
            self._refine_skills(pdf_path, base_data),
        ]

        refinements = await asyncio.gather(*refinement_tasks, return_exceptions=True)

        # Merge refinements into base data
        for refinement in refinements:
            if isinstance(refinement, Exception):
                logger.warning(f"Section refinement failed: {refinement}")
            elif refinement:
                self._merge_refinement(base_data, refinement)

        return {
            "success": True,
            "data": base_data,
            "method": "progressive_extraction",
        }

    async def _refine_education(
        self, pdf_path: Path, base_data: UserLLMSchema
    ) -> Optional[Dict]:
        """Refine education section extraction."""
        try:
            if len(base_data.educations) < 1:
                # If no education found, try dedicated extraction
                education_data = await self.education_extractor.extract_from_pdf(
                    pdf_path,
                    "Extract ALL education experiences, degrees, and certifications.",
                )
                return {"educations": education_data.education_entries}
        except Exception as e:
            logger.error(f"Education refinement failed: {e}")
        return None

    async def _refine_work(
        self, pdf_path: Path, base_data: UserLLMSchema
    ) -> Optional[Dict]:
        """Refine work experience section extraction."""
        try:
            if len(base_data.work_experiences) < 1:
                work_data = await self.work_extractor.extract_from_pdf(
                    pdf_path,
                    "Extract ALL work experiences with detailed responsibilities.",
                )
                return {"work_experiences": work_data.work_entries}
        except Exception as e:
            logger.error(f"Work refinement failed: {e}")
        return None

    async def _refine_projects(
        self, pdf_path: Path, base_data: UserLLMSchema
    ) -> Optional[Dict]:
        """Refine projects section extraction."""
        try:
            if len(base_data.projects) < 1:
                project_data = await self.project_extractor.extract_from_pdf(
                    pdf_path, "Extract ALL projects with tasks and technologies."
                )
                return {"projects": project_data.project_entries}
        except Exception as e:
            logger.error(f"Project refinement failed: {e}")
        return None

    async def _refine_skills(
        self, pdf_path: Path, base_data: UserLLMSchema
    ) -> Optional[Dict]:
        """Refine skills section extraction."""
        try:
            if len(base_data.skills) < 3:  # Assume most resumes have 3+ skills
                skill_data = await self.skill_extractor.extract_from_pdf(
                    pdf_path, "Extract ALL skills, technologies, and competencies."
                )
                return {"skills": skill_data.skill_entries}
        except Exception as e:
            logger.error(f"Skill refinement failed: {e}")
        return None

    def _merge_refinement(self, base_data: UserLLMSchema, refinement: Dict) -> None:
        """Merge refinement data into base data."""
        for key, value in refinement.items():
            if value and hasattr(base_data, key):
                setattr(base_data, key, value)

    def _calculate_section_confidence(self, data: UserLLMSchema) -> Dict[str, float]:
        """Calculate confidence scores for each section."""
        scores = {
            "contact": self._score_contact(data),
            "education": self._score_list_field(data.educations),
            "work": self._score_list_field(data.work_experiences),
            "projects": self._score_list_field(data.projects),
            "skills": self._score_list_field(data.skills),
        }

        scores["overall"] = sum(scores.values()) / len(scores)
        return scores

    def _score_contact(self, data: UserLLMSchema) -> float:
        """Score contact information completeness."""
        fields = [
            data.first_name or data.full_name,
            data.email,
            data.phone,
            data.location,
        ]
        return sum(1 for f in fields if f) / len(fields)

    def _score_list_field(self, items: List) -> float:
        """Score list field based on count and completeness."""
        if not items:
            return 0.0

        # Base score from having items
        base_score = min(len(items) / 3, 1.0)  # Normalize to max of 3 items

        # Completeness score for items
        if items and hasattr(items[0], "model_fields"):
            completeness = sum(
                self.calculate_extraction_confidence(item) for item in items
            ) / len(items)
            return (base_score + completeness) / 2

        return base_score

    def _validate_sections(self, data: UserLLMSchema) -> Dict[str, Any]:
        """Validate each section of extracted data."""
        validation = {
            "has_contact": bool(data.email or data.phone),
            "has_name": bool(data.first_name or data.full_name),
            "has_education": len(data.educations) > 0,
            "has_work": len(data.work_experiences) > 0,
            "has_skills": len(data.skills) > 0,
            "missing_sections": [],
        }

        if not validation["has_contact"]:
            validation["missing_sections"].append("contact")
        if not validation["has_name"]:
            validation["missing_sections"].append("name")
        if not validation["has_education"]:
            validation["missing_sections"].append("education")

        validation["is_complete"] = len(validation["missing_sections"]) == 0

        return validation

    async def extract_section(
        self,
        pdf_path: Path,
        section: str,
    ) -> Dict[str, Any]:
        """Extract a specific section from the resume.

        Args:
            pdf_path: Path to the PDF resume.
            section: Section to extract (education, work, projects, skills, contact).

        Returns:
            Dictionary with extracted section data.
        """
        extractors = {
            "education": self.education_extractor,
            "work": self.work_extractor,
            "projects": self.project_extractor,
            "skills": self.skill_extractor,
            "contact": self.contact_extractor,
        }

        if section not in extractors:
            return {
                "success": False,
                "error": f"Unknown section: {section}",
            }

        try:
            extractor = extractors[section]
            data = await extractor.extract_from_pdf(pdf_path)

            return {
                "success": True,
                "section": section,
                "data": data,
                "confidence": self.calculate_extraction_confidence(data),
            }
        except Exception as e:
            logger.error(f"Failed to extract {section}: {str(e)}")
            return {
                "success": False,
                "section": section,
                "error": str(e),
            }
