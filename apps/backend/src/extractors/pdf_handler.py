"""PDF file handling utilities for resume extraction."""

from pathlib import Path
from typing import List, Optional, Dict, Any
import hashlib
import logging
from datetime import datetime
import aiofiles
import tempfile

logger = logging.getLogger(__name__)


class PDFHandler:
    """Handle PDF file operations for resume extraction."""
    
    def __init__(self, temp_dir: Optional[Path] = None):
        """Initialize PDF handler.
        
        Args:
            temp_dir: Directory for temporary file storage.
        """
        self.temp_dir = temp_dir or Path(tempfile.gettempdir()) / "resume_extraction"
        self.temp_dir.mkdir(exist_ok=True, parents=True)
    
    async def validate_pdf(self, pdf_path: Path) -> Dict[str, Any]:
        """Validate a PDF file for extraction.
        
        Args:
            pdf_path: Path to the PDF file.
            
        Returns:
            Validation result dictionary.
        """
        validation = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "file_info": {},
        }
        
        # Check file exists
        if not pdf_path.exists():
            validation["valid"] = False
            validation["errors"].append(f"File not found: {pdf_path}")
            return validation
        
        # Check file extension
        if pdf_path.suffix.lower() != ".pdf":
            validation["valid"] = False
            validation["errors"].append(f"Not a PDF file: {pdf_path.suffix}")
            return validation
        
        # Get file info
        file_stat = pdf_path.stat()
        validation["file_info"] = {
            "path": str(pdf_path),
            "name": pdf_path.name,
            "size_bytes": file_stat.st_size,
            "size_mb": round(file_stat.st_size / (1024 * 1024), 2),
            "modified": datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
        }
        
        # Check file size
        max_size_mb = 10
        if validation["file_info"]["size_mb"] > max_size_mb:
            validation["warnings"].append(
                f"File size ({validation['file_info']['size_mb']} MB) exceeds recommended maximum ({max_size_mb} MB)"
            )
        
        if validation["file_info"]["size_mb"] == 0:
            validation["valid"] = False
            validation["errors"].append("PDF file is empty")
        
        logger.info(f"PDF validation for {pdf_path.name}: {validation['valid']}")
        return validation
    
    async def save_uploaded_pdf(
        self,
        file_content: bytes,
        filename: str,
    ) -> Path:
        """Save uploaded PDF content to temporary file.
        
        Args:
            file_content: PDF file content as bytes.
            filename: Original filename.
            
        Returns:
            Path to saved temporary file.
        """
        # Generate unique filename
        file_hash = hashlib.md5(file_content).hexdigest()[:8]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_filename = f"{timestamp}_{file_hash}_{filename}"
        
        temp_path = self.temp_dir / safe_filename
        
        async with aiofiles.open(temp_path, "wb") as f:
            await f.write(file_content)
        
        logger.info(f"Saved uploaded PDF to {temp_path}")
        return temp_path
    
    async def download_pdf_from_url(
        self,
        url: str,
        filename: Optional[str] = None,
    ) -> Path:
        """Download PDF from URL to temporary file.
        
        Args:
            url: URL to download PDF from.
            filename: Optional filename for the downloaded file.
            
        Returns:
            Path to downloaded file.
        """
        import aiohttp
        
        if not filename:
            # Extract filename from URL or generate one
            filename = url.split("/")[-1] or "downloaded_resume.pdf"
            if not filename.endswith(".pdf"):
                filename += ".pdf"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                response.raise_for_status()
                content = await response.read()
        
        return await self.save_uploaded_pdf(content, filename)
    
    def cleanup_temp_file(self, file_path: Path) -> bool:
        """Remove a temporary file.
        
        Args:
            file_path: Path to file to remove.
            
        Returns:
            True if file was removed, False otherwise.
        """
        try:
            if file_path.exists() and file_path.parent == self.temp_dir:
                file_path.unlink()
                logger.info(f"Cleaned up temporary file: {file_path}")
                return True
        except Exception as e:
            logger.error(f"Failed to cleanup {file_path}: {e}")
        return False
    
    def cleanup_old_files(self, max_age_hours: int = 24) -> int:
        """Clean up old temporary files.
        
        Args:
            max_age_hours: Maximum age of files to keep in hours.
            
        Returns:
            Number of files cleaned up.
        """
        from datetime import timedelta
        
        count = 0
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        
        for file_path in self.temp_dir.glob("*.pdf"):
            file_stat = file_path.stat()
            file_time = datetime.fromtimestamp(file_stat.st_mtime)
            
            if file_time < cutoff_time:
                if self.cleanup_temp_file(file_path):
                    count += 1
        
        if count > 0:
            logger.info(f"Cleaned up {count} old temporary files")
        
        return count
    
    def get_pdf_files_from_directory(
        self,
        directory: Path,
        pattern: str = "*.pdf",
    ) -> List[Path]:
        """Get all PDF files from a directory.
        
        Args:
            directory: Directory to search.
            pattern: Glob pattern for PDF files.
            
        Returns:
            List of PDF file paths.
        """
        if not directory.exists():
            logger.warning(f"Directory does not exist: {directory}")
            return []
        
        pdf_files = list(directory.glob(pattern))
        logger.info(f"Found {len(pdf_files)} PDF files in {directory}")
        return pdf_files
    
    async def batch_validate(
        self,
        pdf_paths: List[Path],
    ) -> Dict[str, Any]:
        """Validate multiple PDF files.
        
        Args:
            pdf_paths: List of PDF file paths.
            
        Returns:
            Batch validation results.
        """
        import asyncio
        
        validation_tasks = [
            self.validate_pdf(pdf_path) for pdf_path in pdf_paths
        ]
        
        results = await asyncio.gather(*validation_tasks)
        
        valid_files = [
            pdf_paths[i] for i, r in enumerate(results) if r["valid"]
        ]
        invalid_files = [
            {
                "path": pdf_paths[i],
                "errors": r["errors"],
            }
            for i, r in enumerate(results)
            if not r["valid"]
        ]
        
        return {
            "total": len(pdf_paths),
            "valid_count": len(valid_files),
            "invalid_count": len(invalid_files),
            "valid_files": valid_files,
            "invalid_files": invalid_files,
            "validation_details": results,
        }
    
    def calculate_file_hash(self, file_path: Path) -> str:
        """Calculate hash of a file for deduplication.
        
        Args:
            file_path: Path to file.
            
        Returns:
            MD5 hash of file content.
        """
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def deduplicate_files(self, pdf_paths: List[Path]) -> List[Path]:
        """Remove duplicate PDF files based on content hash.
        
        Args:
            pdf_paths: List of PDF file paths.
            
        Returns:
            List of unique PDF file paths.
        """
        seen_hashes = set()
        unique_files = []
        
        for pdf_path in pdf_paths:
            try:
                file_hash = self.calculate_file_hash(pdf_path)
                if file_hash not in seen_hashes:
                    seen_hashes.add(file_hash)
                    unique_files.append(pdf_path)
                else:
                    logger.info(f"Skipping duplicate file: {pdf_path.name}")
            except Exception as e:
                logger.error(f"Error hashing {pdf_path}: {e}")
                unique_files.append(pdf_path)  # Include files that can't be hashed
        
        logger.info(
            f"Deduplication: {len(pdf_paths)} files -> {len(unique_files)} unique"
        )
        return unique_files