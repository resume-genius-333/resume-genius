"""Unified extraction service for resume processing."""

from pathlib import Path
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
import logging
import asyncio
from enum import Enum

from src.extractors import ResumeExtractor, PDFHandler
from src.schemas.llm.user import UserLLMSchema

logger = logging.getLogger(__name__)


class ExtractionStatus(Enum):
    """Status of extraction job."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"


class ExtractionJob:
    """Represents an extraction job."""
    
    def __init__(self, job_id: str, file_path: Path):
        self.job_id = job_id
        self.file_path = file_path
        self.status = ExtractionStatus.PENDING
        self.created_at = datetime.now()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.result: Optional[Dict[str, Any]] = None
        self.error: Optional[str] = None
        self.progress: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert job to dictionary."""
        return {
            "job_id": self.job_id,
            "file_path": str(self.file_path),
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "progress": self.progress,
            "error": self.error,
        }


class ExtractionService:
    """Service for managing resume extraction operations."""
    
    def __init__(
        self,
        model: str = "gpt-5-nano",
        max_retries: int = 2,
        use_progressive: bool = True,
        temp_dir: Optional[Path] = None,
    ):
        """Initialize extraction service.
        
        Args:
            model: Model to use for extraction.
            max_retries: Maximum retries for failed extractions.
            use_progressive: Whether to use progressive extraction.
            temp_dir: Directory for temporary files.
        """
        self.model = model
        self.max_retries = max_retries
        self.use_progressive = use_progressive
        
        self.pdf_handler = PDFHandler(temp_dir)
        self.resume_extractor = ResumeExtractor(
            model=model,
            max_retries=max_retries,
            use_progressive_extraction=use_progressive,
        )
        
        self.jobs: Dict[str, ExtractionJob] = {}
        self._job_counter = 0
    
    def _generate_job_id(self) -> str:
        """Generate unique job ID."""
        self._job_counter += 1
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        return f"job_{timestamp}_{self._job_counter:04d}"
    
    async def extract_from_file(
        self,
        file_path: Union[Path, str],
        validate: bool = True,
        async_mode: bool = False,
    ) -> Dict[str, Any]:
        """Extract resume data from a file.
        
        Args:
            file_path: Path to PDF file.
            validate: Whether to validate extracted data.
            async_mode: Whether to run asynchronously (returns job ID).
            
        Returns:
            Extraction result or job information if async.
        """
        file_path = Path(file_path)
        
        # Validate PDF
        validation = await self.pdf_handler.validate_pdf(file_path)
        if not validation["valid"]:
            return {
                "success": False,
                "errors": validation["errors"],
            }
        
        if async_mode:
            # Create job and return immediately
            job_id = self._generate_job_id()
            job = ExtractionJob(job_id, file_path)
            self.jobs[job_id] = job
            
            # Start extraction in background
            asyncio.create_task(self._process_job(job, validate))
            
            return {
                "success": True,
                "job_id": job_id,
                "status": "pending",
                "message": "Extraction job created",
            }
        else:
            # Extract synchronously
            result = await self.resume_extractor.extract_full_resume(
                file_path,
                validate_sections=validate,
            )
            return result
    
    async def _process_job(self, job: ExtractionJob, validate: bool) -> None:
        """Process extraction job asynchronously."""
        try:
            job.status = ExtractionStatus.IN_PROGRESS
            job.started_at = datetime.now()
            job.progress = 0.1
            
            result = await self.resume_extractor.extract_full_resume(
                job.file_path,
                validate_sections=validate,
            )
            
            job.result = result
            job.status = (
                ExtractionStatus.COMPLETED
                if result.get("success")
                else ExtractionStatus.FAILED
            )
            job.progress = 1.0
            
        except Exception as e:
            logger.error(f"Job {job.job_id} failed: {e}")
            job.status = ExtractionStatus.FAILED
            job.error = str(e)
            
        finally:
            job.completed_at = datetime.now()
    
    async def extract_from_url(
        self,
        pdf_url: str,
        validate: bool = True,
    ) -> Dict[str, Any]:
        """Extract resume data from a URL.
        
        Args:
            pdf_url: URL to PDF file.
            validate: Whether to validate extracted data.
            
        Returns:
            Extraction result.
        """
        try:
            # Download PDF to temp file
            temp_path = await self.pdf_handler.download_pdf_from_url(pdf_url)
            
            # Extract from temp file
            result = await self.extract_from_file(temp_path, validate)
            
            # Cleanup temp file
            self.pdf_handler.cleanup_temp_file(temp_path)
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to extract from URL: {e}")
            return {
                "success": False,
                "error": str(e),
            }
    
    async def extract_section(
        self,
        file_path: Union[Path, str],
        section: str,
    ) -> Dict[str, Any]:
        """Extract specific section from resume.
        
        Args:
            file_path: Path to PDF file.
            section: Section to extract.
            
        Returns:
            Section extraction result.
        """
        file_path = Path(file_path)
        
        # Validate PDF
        validation = await self.pdf_handler.validate_pdf(file_path)
        if not validation["valid"]:
            return {
                "success": False,
                "errors": validation["errors"],
            }
        
        return await self.resume_extractor.extract_section(file_path, section)
    
    async def batch_extract(
        self,
        directory: Union[Path, str],
        pattern: str = "*.pdf",
        validate: bool = True,
        max_concurrent: int = 5,
    ) -> Dict[str, Any]:
        """Extract from multiple PDF files in a directory.
        
        Args:
            directory: Directory containing PDF files.
            pattern: Glob pattern for PDF files.
            validate: Whether to validate each extraction.
            max_concurrent: Maximum concurrent extractions.
            
        Returns:
            Batch extraction results.
        """
        directory = Path(directory)
        
        # Get PDF files
        pdf_files = self.pdf_handler.get_pdf_files_from_directory(
            directory, pattern
        )
        
        if not pdf_files:
            return {
                "success": False,
                "error": "No PDF files found",
            }
        
        # Deduplicate files
        unique_files = self.pdf_handler.deduplicate_files(pdf_files)
        
        # Validate all files
        batch_validation = await self.pdf_handler.batch_validate(unique_files)
        valid_files = batch_validation["valid_files"]
        
        if not valid_files:
            return {
                "success": False,
                "error": "No valid PDF files",
                "validation": batch_validation,
            }
        
        # Process in batches with concurrency limit
        results = []
        for i in range(0, len(valid_files), max_concurrent):
            batch = valid_files[i : i + max_concurrent]
            batch_results = await asyncio.gather(
                *[
                    self.extract_from_file(file_path, validate)
                    for file_path in batch
                ],
                return_exceptions=True,
            )
            
            for file_path, result in zip(batch, batch_results):
                if isinstance(result, Exception):
                    results.append({
                        "file": file_path.name,
                        "success": False,
                        "error": str(result),
                    })
                else:
                    results.append({
                        "file": file_path.name,
                        **result,
                    })
        
        successful = sum(1 for r in results if r.get("success"))
        
        return {
            "success": True,
            "total_files": len(valid_files),
            "successful": successful,
            "failed": len(valid_files) - successful,
            "results": results,
            "validation": batch_validation,
        }
    
    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get status of extraction job.
        
        Args:
            job_id: Job identifier.
            
        Returns:
            Job status and result if completed.
        """
        job = self.jobs.get(job_id)
        if not job:
            return None
        
        response = job.to_dict()
        
        if job.status == ExtractionStatus.COMPLETED and job.result:
            response["result"] = job.result
        
        return response
    
    def list_jobs(
        self,
        status: Optional[ExtractionStatus] = None,
    ) -> List[Dict[str, Any]]:
        """List extraction jobs.
        
        Args:
            status: Filter by status.
            
        Returns:
            List of job information.
        """
        jobs = self.jobs.values()
        
        if status:
            jobs = [j for j in jobs if j.status == status]
        
        return [j.to_dict() for j in jobs]
    
    def cleanup_jobs(self, max_age_hours: int = 24) -> int:
        """Clean up old completed jobs.
        
        Args:
            max_age_hours: Maximum age of jobs to keep.
            
        Returns:
            Number of jobs cleaned up.
        """
        from datetime import timedelta
        
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        jobs_to_remove = []
        
        for job_id, job in self.jobs.items():
            if (
                job.completed_at
                and job.completed_at < cutoff_time
                and job.status in [ExtractionStatus.COMPLETED, ExtractionStatus.FAILED]
            ):
                jobs_to_remove.append(job_id)
        
        for job_id in jobs_to_remove:
            del self.jobs[job_id]
        
        if jobs_to_remove:
            logger.info(f"Cleaned up {len(jobs_to_remove)} old jobs")
        
        return len(jobs_to_remove)
    
    async def export_to_json(
        self,
        data: UserLLMSchema,
        output_path: Union[Path, str],
        pretty: bool = True,
    ) -> bool:
        """Export extracted data to JSON file.
        
        Args:
            data: Extracted resume data.
            output_path: Path for output JSON file.
            pretty: Whether to format JSON nicely.
            
        Returns:
            True if successful.
        """
        import json
        import aiofiles
        
        try:
            output_path = Path(output_path)
            json_data = data.model_dump(exclude_none=True)
            
            async with aiofiles.open(output_path, "w") as f:
                if pretty:
                    await f.write(json.dumps(json_data, indent=2))
                else:
                    await f.write(json.dumps(json_data))
            
            logger.info(f"Exported data to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export data: {e}")
            return False