"""Contact information extractor."""

from typing import Optional
from pydantic import BaseModel, Field, EmailStr, HttpUrl

from src.models.base import BaseLLMSchema
from src.extractors.base_extractor import BaseExtractor


class ContactSchema(BaseLLMSchema):
    """Schema for extracting contact information."""

    first_name: Optional[str] = Field(None, description="Person's first name")

    last_name: Optional[str] = Field(None, description="Person's last name")

    full_name: Optional[str] = Field(
        None, description="Person's full name if first/last not clearly separated"
    )

    name_prefix: Optional[str] = Field(
        None, description="Name prefix or title (Dr., Mr., Ms., Prof., etc.)"
    )

    name_suffix: Optional[str] = Field(
        None, description="Name suffix (Jr., Sr., III, PhD, MD, etc.)"
    )

    email: Optional[EmailStr] = Field(None, description="Email address")

    phone: Optional[str] = Field(None, description="Phone number in any format")

    location: Optional[str] = Field(
        None, description="Current location (city, state, country)"
    )

    linkedin_url: Optional[HttpUrl] = Field(None, description="LinkedIn profile URL")

    github_url: Optional[HttpUrl] = Field(None, description="GitHub profile URL")

    portfolio_url: Optional[HttpUrl] = Field(
        None, description="Personal website or portfolio URL"
    )

    summary: Optional[str] = Field(
        None, description="Professional summary or objective"
    )

    extraction_notes: Optional[str] = Field(
        None, description="Any notes about the extraction"
    )


class ContactExtractor(BaseExtractor[ContactSchema]):
    """Extractor for contact information and personal details."""

    def get_extraction_prompt(self) -> str:
        """Get the prompt for contact information extraction."""
        return """Extract ALL contact and personal information from this resume including:
        
        1. Name Information:
           - First name and last name (try to separate if possible)
           - Full name (if first/last cannot be clearly separated)
           - Any titles or prefixes (Dr., Prof., Mr., Ms., etc.)
           - Any suffixes (Jr., Sr., III, PhD, MD, etc.)
        
        2. Contact Details:
           - Email address
           - Phone number (in any format)
           - Current location (city, state, country)
           - Mailing address if provided
        
        3. Online Presence:
           - LinkedIn profile URL
           - GitHub profile URL
           - Personal website or portfolio URL
           - Twitter/X handle if professional
           - Other professional social media or platforms
        
        4. Professional Summary:
           - Career objective or summary statement
           - Professional headline or tagline
           - About section content
        
        IMPORTANT:
        - Extract the exact URLs for online profiles
        - Preserve phone number format as given
        - Include location even if just city or country
        - Capture the full professional summary if present
        
        Be thorough in extracting all contact and identification information."""

    def get_response_model(self):
        """Get the response model for contact extraction."""
        return ContactSchema
