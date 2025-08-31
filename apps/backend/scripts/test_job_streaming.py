#!/usr/bin/env python3
"""
Testing script for job creation and SSE streaming.

This script supports both manual interactive testing and automated testing modes.

Manual mode (default):
- Creates a job and streams events interactively
- Displays real-time updates
- Can be interrupted with Ctrl+C

Automated mode:
- Runs with assertions and timeouts
- Returns exit code 0 on success, 1 on failure
- Suitable for CI/CD pipelines

Usage:
    # Manual interactive mode
    python scripts/test_job_streaming.py
    
    # Automated test mode
    python scripts/test_job_streaming.py --automated
    
    # Custom configuration
    python scripts/test_job_streaming.py --host http://localhost:8000 --user-id test-user-123

Example:
    python scripts/test_job_streaming.py
    python scripts/test_job_streaming.py --automated --timeout 30
"""

# Disable proxy for localhost connections
import os
os.environ['NO_PROXY'] = '*'
os.environ['no_proxy'] = '*'

import asyncio
import json
import sys
from datetime import datetime
from typing import Optional
import argparse
import signal

import httpx


class JobStreamingTester:
    def __init__(self, base_url: str = "http://127.0.0.1:8000", user_id: str = "test-user", automated: bool = False):
        self.base_url = base_url.rstrip("/")
        self.user_id = user_id
        self.client = httpx.AsyncClient(timeout=30.0)
        self.stop_event = asyncio.Event()
        self.automated = automated
        self.job_completed = False
        self.events_received: list = []
        
    def log(self, message: str, level: str = "INFO"):
        """Log message with timestamp."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        print(f"[{timestamp}] [{level}] {message}")
    
    async def create_job(self, job_description: str, job_url: Optional[str] = None) -> str:
        """Create a job and return the job_id."""
        self.log(f"Creating job for user: {self.user_id}")
        
        payload = {
            "job_description": job_description,
            "job_url": job_url
        }
        
        try:
            response = await self.client.post(
                f"{self.base_url}/users/{self.user_id}/jobs/create",
                json=payload
            )
            response.raise_for_status()
            
            data = response.json()
            job_id = data["job_id"]
            self.log(f"Job created successfully with ID: {job_id}", "SUCCESS")
            return job_id
            
        except httpx.HTTPError as e:
            self.log(f"Failed to create job: {e}", "ERROR")
            raise
    
    async def stream_job_status(self, job_id: str, timeout: Optional[int] = None):
        """Connect to SSE endpoint and stream job status updates."""
        url = f"{self.base_url}/api/v1/users/{self.user_id}/jobs/{job_id}/status"
        self.log(f"Connecting to SSE endpoint: {url}")
        
        stream_timeout = timeout or (30 if self.automated else None)
        
        async def stream_events(url):
            """Helper function to stream events."""
            async with self.client.stream("GET", url) as response:
                response.raise_for_status()
                
                self.log("Connected to SSE stream", "SUCCESS")
                if not self.automated:
                    self.log("Waiting for events... (Press Ctrl+C to stop)")
                
                async for line in response.aiter_lines():
                    if self.stop_event.is_set():
                        break
                        
                    if not line:
                        continue
                    
                    if line.startswith("data: "):
                        event_data = line[6:]  # Remove "data: " prefix
                        self.handle_event(event_data)
                        
                        # In automated mode, stop after receiving job completion
                        if self.automated and self.job_completed:
                            self.log("Job processing completed, stopping stream", "SUCCESS")
                            break
        
        try:
            if stream_timeout:
                async with asyncio.timeout(stream_timeout):
                    await stream_events(url)
            else:
                await stream_events(url)
                                
        except asyncio.TimeoutError:
            if self.automated:
                self.log(f"Timeout after {stream_timeout}s waiting for job completion", "ERROR")
                raise
            else:
                self.log(f"Stream timeout after {stream_timeout}s", "WARNING")
        except httpx.HTTPError as e:
            self.log(f"SSE connection error: {e}", "ERROR")
            raise
        except KeyboardInterrupt:
            self.log("Stream interrupted by user", "INFO")
        finally:
            self.log("SSE connection closed", "INFO")
    
    def handle_event(self, event_data: str):
        """Handle received SSE event."""
        try:
            # Try to parse as JSON
            data = json.loads(event_data)
            self.events_received.append(data)
            self.log("Received event:", "EVENT")
            
            # Pretty print the JSON data
            if not self.automated:
                formatted = json.dumps(data, indent=2)
                for line in formatted.split("\n"):
                    print(f"  {line}")
            
            # Check for job data (contains extracted information)
            if isinstance(data, dict):
                if "title" in data:
                    self.job_completed = True
                    self.log(f"Job extracted successfully - Title: {data.get('title')}", "SUCCESS")
                    if "company_name" in data:
                        self.log(f"Company: {data.get('company_name')}", "INFO")
                    if "skills" in data and data["skills"]:
                        skills_preview = ", ".join(data["skills"][:5])
                        self.log(f"Skills: {skills_preview}", "INFO")
                elif data.get("status") == "error":
                    self.log(f"Job processing failed: {data.get('error', 'Unknown error')}", "ERROR")
                    if self.automated:
                        raise Exception(f"Job processing failed: {data.get('error')}")
                    
        except json.JSONDecodeError:
            # If not JSON, just print the raw data
            self.log(f"Received raw event: {event_data}", "EVENT")
            self.events_received.append(event_data)
    
    async def run_test(self, job_description: str, job_url: Optional[str] = None, timeout: int = 30):
        """Run the complete test flow."""
        try:
            # Create job
            job_id = await self.create_job(job_description, job_url)
            
            # Small delay to ensure background task starts
            await asyncio.sleep(0.5)
            
            # Stream status updates
            await self.stream_job_status(job_id, timeout=timeout)
            
            # In automated mode, verify results
            if self.automated:
                if not self.job_completed:
                    raise Exception(f"Job did not complete within {timeout} seconds")
                if len(self.events_received) == 0:
                    raise Exception("No events were received")
                
                self.log("Test completed successfully!", "SUCCESS")
                self.log(f"Total events received: {len(self.events_received)}", "INFO")
                return True
            
        except Exception as e:
            self.log(f"Test failed: {e}", "ERROR")
            if self.automated:
                sys.exit(1)
            raise
        finally:
            await self.client.aclose()
    
    def stop(self):
        """Signal to stop streaming."""
        self.stop_event.set()


async def main():
    parser = argparse.ArgumentParser(description="Test job creation and SSE streaming")
    parser.add_argument(
        "--host",
        default="http://127.0.0.1:8000",
        help="Backend API host (default: http://127.0.0.1:8000)"
    )
    parser.add_argument(
        "--user-id",
        default=None,
        help="User ID for testing (default: auto-generated UUID)"
    )
    parser.add_argument(
        "--job-url",
        default="https://example.com/jobs/software-engineer",
        help="Job URL (optional)"
    )
    parser.add_argument(
        "--job-description",
        help="Custom job description (optional, uses default if not provided)"
    )
    parser.add_argument(
        "--automated",
        action="store_true",
        help="Run in automated mode with assertions and exit codes"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=30,
        help="Timeout in seconds for automated mode (default: 30)"
    )
    
    args = parser.parse_args()
    
    # Default job description if not provided
    default_description = """
    Senior Software Engineer - Backend
    
    We are looking for an experienced Backend Engineer to join our growing team.
    
    Requirements:
    - 5+ years of experience with Python
    - Strong experience with FastAPI, Django, or Flask
    - Expert knowledge of PostgreSQL and database optimization
    - Experience with Redis, RabbitMQ, or similar message brokers
    - Proficiency with Docker and Kubernetes
    - Experience with AWS or GCP
    
    Nice to have:
    - Experience with microservices architecture
    - Knowledge of event-driven systems
    - Experience with GraphQL
    - Contributions to open source projects
    
    What we offer:
    - Competitive salary ($150k - $200k)
    - Full health, dental, and vision insurance
    - Flexible remote work policy
    - 401(k) with company matching
    - Annual learning budget
    - Stock options
    
    Location: San Francisco, CA (Remote OK)
    """
    
    job_description = args.job_description or default_description
    
    # Generate or use provided user ID
    import uuid
    user_id = args.user_id or str(uuid.uuid4())
    
    # Create tester instance
    tester = JobStreamingTester(
        base_url=args.host, 
        user_id=user_id,
        automated=args.automated
    )
    
    # Handle Ctrl+C gracefully (only in manual mode)
    if not args.automated:
        def signal_handler(sig, frame):
            print("\n")
            tester.log("Stopping test...", "INFO")
            tester.stop()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
    
    # Print test configuration
    print("="*60)
    print("Job Creation and SSE Streaming Test")
    if args.automated:
        print("MODE: AUTOMATED")
    else:
        print("MODE: INTERACTIVE")
    print("="*60)
    print(f"Host: {args.host}")
    print(f"User ID: {user_id}")
    print(f"Job URL: {args.job_url}")
    if args.automated:
        print(f"Timeout: {args.timeout}s")
    print("="*60)
    print()
    
    # Run the test
    result = await tester.run_test(job_description, args.job_url, timeout=args.timeout)
    
    # In automated mode, exit with appropriate code
    if args.automated:
        sys.exit(0 if result else 1)


if __name__ == "__main__":
    asyncio.run(main())