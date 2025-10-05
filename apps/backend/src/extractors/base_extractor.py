"""Base extractor class for all extraction operations."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, TypeVar, Generic, List
from pathlib import Path
import instructor
from openai import AsyncOpenAI
from pydantic import BaseModel
from tenacity import retry, stop_after_attempt, wait_exponential
import logging

from src.models.base import BaseLLMSchema

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseLLMSchema)


class BaseExtractor(ABC, Generic[T]):
    """Abstract base class for all extractors."""

    def __init__(
        self,
        client: Optional[instructor.AsyncInstructor] = None,
        model: str = "gpt-5-nano",
        max_retries: int = 2,
    ):
        """Initialize the base extractor.

        Args:
            client: Instructor client instance. If None, will create from environment.
            model: Model to use for extraction.
            max_retries: Maximum number of retries for failed extractions.
        """
        self.client = client or self._create_default_client()
        self.model = model
        self.max_retries = max_retries

    @staticmethod
    def _create_default_client() -> instructor.AsyncInstructor:
        """Create default Instructor client from environment variables."""
        from src.config.settings import get_settings

        settings = get_settings()

        base_url = settings.litellm_base_url()
        api_key = settings.litellm_api_key

        if not api_key:
            raise ValueError("LITELLM_API_KEY must be set in the environment")

        return instructor.from_openai(
            AsyncOpenAI(
                base_url=base_url,
                api_key=api_key,
            )
        )

    @abstractmethod
    def get_extraction_prompt(self) -> str:
        """Get the prompt for extraction.

        Returns:
            The extraction prompt string.
        """
        pass

    @abstractmethod
    def get_response_model(self) -> type[BaseModel]:
        """Get the Pydantic model for the response.

        Returns:
            The response model class.
        """
        pass

    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def extract_from_pdf(
        self,
        pdf_path: Path,
        additional_instructions: Optional[str] = None,
    ) -> T:
        """Extract structured data from a PDF file.

        Args:
            pdf_path: Path to the PDF file.
            additional_instructions: Optional additional instructions for extraction.

        Returns:
            Extracted data as the response model instance.
        """
        from instructor.multimodal import PDF

        prompt = self.get_extraction_prompt()
        if additional_instructions:
            prompt = f"{prompt}\n\nAdditional instructions: {additional_instructions}"

        try:
            result = await self.client.chat.completions.create(
                model=self.model,
                response_model=self.get_response_model(),
                messages=[
                    {"role": "user", "content": [prompt, PDF.from_path(str(pdf_path))]}
                ],
                max_retries=self.max_retries,
            )

            logger.info(
                f"Successfully extracted {self.__class__.__name__} from {pdf_path.name}"
            )
            return result

        except Exception as e:
            logger.error(f"Failed to extract from {pdf_path.name}: {str(e)}")
            raise

    async def extract_from_url(
        self,
        pdf_url: str,
        additional_instructions: Optional[str] = None,
    ) -> T:
        """Extract structured data from a PDF URL.

        Args:
            pdf_url: URL to the PDF file.
            additional_instructions: Optional additional instructions for extraction.

        Returns:
            Extracted data as the response model instance.
        """
        from instructor.multimodal import PDF

        prompt = self.get_extraction_prompt()
        if additional_instructions:
            prompt = f"{prompt}\n\nAdditional instructions: {additional_instructions}"

        try:
            result = await self.client.chat.completions.create(
                model=self.model,
                response_model=self.get_response_model(),
                messages=[{"role": "user", "content": [prompt, PDF.from_url(pdf_url)]}],
                max_retries=self.max_retries,
            )

            logger.info(f"Successfully extracted {self.__class__.__name__} from URL")
            return result

        except Exception as e:
            logger.error(f"Failed to extract from URL: {str(e)}")
            raise

    async def extract_batch(
        self,
        pdf_paths: List[Path],
        additional_instructions: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Extract from multiple PDF files.

        Args:
            pdf_paths: List of paths to PDF files.
            additional_instructions: Optional additional instructions for extraction.

        Returns:
            List of extraction results with file info and data.
        """
        import asyncio

        async def process_single(pdf_path: Path) -> Dict[str, Any]:
            try:
                data = await self.extract_from_pdf(pdf_path, additional_instructions)
                return {
                    "file": pdf_path.name,
                    "success": True,
                    "data": data,
                }
            except Exception as e:
                return {
                    "file": pdf_path.name,
                    "success": False,
                    "error": str(e),
                }

        results = await asyncio.gather(
            *[process_single(pdf_path) for pdf_path in pdf_paths]
        )

        successful = sum(1 for r in results if r["success"])
        logger.info(
            f"Batch extraction complete: {successful}/{len(pdf_paths)} successful"
        )

        return results

    def calculate_extraction_confidence(self, extracted_data: T) -> float:
        """Calculate confidence score for extracted data.

        Args:
            extracted_data: The extracted data instance.

        Returns:
            Confidence score between 0 and 1.
        """
        if not extracted_data:
            return 0.0

        total_fields = len(extracted_data.model_fields)
        filled_fields = sum(
            1
            for field_name in extracted_data.model_fields
            if getattr(extracted_data, field_name, None) is not None
        )

        return filled_fields / total_fields if total_fields > 0 else 0.0
