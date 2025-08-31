#!/usr/bin/env python3
"""
Testing script for job creation and SSE streaming with user authentication.

This script:
1. Creates a test user via registration
2. Creates a job for that user
3. Streams events from the SSE endpoint

Usage:
    python scripts/test_job_streaming_with_auth.py
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
import uuid

import httpx


async def create_test_user(client: httpx.AsyncClient, base_url: str):
    """Create a test user and return the user ID."""
    email = f"test_{uuid.uuid4().hex[:8]}@example.com"
    password = "TestPassword123!"
    
    print(f"Creating test user with email: {email}")
    
    response = await client.post(
        f"{base_url}/api/v1/auth/register",
        json={
            "email": email,
            "password": password,
            "first_name": "Test",
            "last_name": "User"
        }
    )
    
    if response.status_code == 201:
        data = response.json()
        print(f"✓ User created successfully with ID: {data.get('user_id')}")
        return data.get("user_id"), data.get("access_token")
    else:
        print(f"✗ Failed to create user: {response.status_code} - {response.text}")
        return None, None


async def create_job(client: httpx.AsyncClient, base_url: str, user_id: str, token: Optional[str] = None):
    """Create a job for the user."""
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    print(f"Creating job for user: {user_id}")
    
    response = await client.post(
        f"{base_url}/api/v1/users/{user_id}/jobs/create",
        json={
            "job_description": """
            Senior Software Engineer
            
            We are looking for an experienced engineer.
            
            Requirements:
            - 5+ years of Python experience
            - FastAPI knowledge
            - PostgreSQL and Redis experience
            """,
            "job_url": "https://example.com/jobs/senior-engineer"
        },
        headers=headers
    )
    
    if response.status_code == 200:
        data = response.json()
        job_id = data["job_id"]
        print(f"✓ Job created with ID: {job_id}")
        return job_id
    else:
        print(f"✗ Failed to create job: {response.status_code} - {response.text}")
        return None


async def stream_job_events(client: httpx.AsyncClient, base_url: str, user_id: str, job_id: str):
    """Stream events from the SSE endpoint."""
    url = f"{base_url}/api/v1/users/{user_id}/jobs/{job_id}/status"
    print(f"Connecting to SSE stream: {url}")
    
    try:
        async with asyncio.timeout(30):
            async with client.stream("GET", url) as response:
                if response.status_code != 200:
                    print(f"✗ Failed to connect: {response.status_code}")
                    return False
                    
                print("✓ Connected to SSE stream")
                print("Waiting for events (max 30s)...")
                
                event_count = 0
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        event_data = line[6:]
                        event_count += 1
                        
                        try:
                            data = json.loads(event_data)
                            print(f"\nEvent {event_count} received:")
                            
                            if isinstance(data, dict):
                                if "title" in data:
                                    print(f"  Job Title: {data.get('title')}")
                                    print(f"  Company: {data.get('company_name', 'N/A')}")
                                    if data.get("skills"):
                                        print(f"  Skills: {', '.join(data['skills'][:5])}")
                                    print("\n✅ Job processing completed successfully!")
                                    return True
                                else:
                                    print(f"  Data: {json.dumps(data, indent=2)}")
                        except json.JSONDecodeError:
                            print(f"  Raw data: {event_data}")
                            
    except asyncio.TimeoutError:
        print("\n⚠ Timeout: No completion event received within 30 seconds")
        return False
    except Exception as e:
        print(f"\n✗ Error: {e}")
        return False


async def main():
    base_url = "http://127.0.0.1:8000"
    
    print("="*60)
    print("Job Creation and SSE Streaming Test (with Authentication)")
    print("="*60)
    print(f"Host: {base_url}")
    print(f"Time: {datetime.now().isoformat()}")
    print("="*60)
    print()
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Step 1: Create a test user
        user_id, token = await create_test_user(client, base_url)
        if not user_id:
            print("\n❌ Test failed: Could not create user")
            sys.exit(1)
        
        # Step 2: Create a job
        job_id = await create_job(client, base_url, user_id, token)
        if not job_id:
            print("\n❌ Test failed: Could not create job")
            sys.exit(1)
        
        # Small delay to let background processing start
        await asyncio.sleep(1)
        
        # Step 3: Stream events
        success = await stream_job_events(client, base_url, user_id, job_id)
        
        if success:
            print("\n✅ All tests passed!")
            sys.exit(0)
        else:
            print("\n❌ Test failed: Did not receive expected events")
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())