"""
Integration test configuration.

These tests require the backend to be running at http://localhost:8000.
Run `just up` before running these tests.
"""

# Disable proxy for localhost connections
import os
os.environ['NO_PROXY'] = '*'
os.environ['no_proxy'] = '*'

import pytest
import httpx
import asyncio


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def api_client():
    """Create an HTTP client for API testing."""
    return httpx.AsyncClient(
        base_url="http://127.0.0.1:8000",
        timeout=30.0,
        headers={"Content-Type": "application/json"}
    )


@pytest.fixture
def test_user_id():
    """Generate a unique user ID for testing."""
    import uuid
    return str(uuid.uuid4())


@pytest.fixture
def sample_job_description():
    """Sample job description for testing."""
    return """
    Senior Backend Engineer
    
    We are looking for an experienced Backend Engineer.
    
    Requirements:
    - 5+ years of Python experience
    - Strong knowledge of FastAPI
    - Experience with PostgreSQL and Redis
    - Docker and Kubernetes expertise
    
    Benefits:
    - Competitive salary
    - Remote work
    - Health insurance
    """