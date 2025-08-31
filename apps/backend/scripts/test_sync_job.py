#!/usr/bin/env python3
"""Test the synchronous job creation endpoint to debug issues."""

import os
import sys
import requests
import json
import uuid

# Bypass proxy
os.environ['NO_PROXY'] = '*'

def test_sync_job_creation():
    """Test the synchronous job creation endpoint."""
    base_url = "http://localhost:8000"
    
    # Create session without proxy
    session = requests.Session()
    session.trust_env = False
    
    # First create a user
    email = f"test_{uuid.uuid4().hex[:8]}@example.com"
    password = "TestPassword123!"
    
    print(f"Creating user with email: {email}")
    
    # Register user
    response = session.post(
        f"{base_url}/api/v1/auth/register",
        json={
            "email": email,
            "password": password,
            "first_name": "Test",
            "last_name": "User"
        }
    )
    
    if response.status_code not in [200, 201]:
        print(f"Failed to create user: {response.status_code}")
        print(response.text)
        sys.exit(1)
    
    user_data = response.json()
    user_id = user_data.get("user_id") or user_data.get("id")
    print(f"Created user: {user_id}")
    
    # Now test the synchronous job creation
    print("\nTesting synchronous job creation...")
    
    job_description = """
    Senior Software Engineer at TechCorp
    
    Requirements:
    - 5+ years of Python experience
    - Experience with FastAPI and SQLAlchemy
    - Strong knowledge of PostgreSQL
    - Experience with Redis and caching
    - Understanding of async programming
    
    Responsibilities:
    - Design and implement backend services
    - Write clean, maintainable code
    - Collaborate with frontend team
    - Participate in code reviews
    """
    
    response = session.post(
        f"{base_url}/api/v1/users/{user_id}/jobs/create_sync",
        json={
            "job_description": job_description,
            "job_url": "https://example.com/job/123"
        }
    )
    
    print(f"Response status: {response.status_code}")
    result = response.json()
    print(f"Response body:\n{json.dumps(result, indent=2)}")
    
    if result.get("status") == "error":
        print("\n❌ Job creation failed!")
        print(f"Error: {result.get('error')}")
        print(f"Traceback:\n{result.get('traceback')}")
    else:
        print("\n✅ Job created successfully!")
        print(f"Job ID: {result.get('job_id')}")

if __name__ == "__main__":
    test_sync_job_creation()