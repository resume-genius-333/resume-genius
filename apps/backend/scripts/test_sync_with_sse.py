#!/usr/bin/env python3
"""Test synchronous job creation with SSE streaming."""

import os
import sys
import requests
import json
import uuid
import threading
import time

# Bypass proxy
os.environ['NO_PROXY'] = '*'

def stream_sse_events(base_url, user_id, job_id, session):
    """Stream SSE events in a thread."""
    print(f"\n📡 Starting SSE stream for job {job_id}...")
    
    try:
        response = session.get(
            f"{base_url}/api/v1/users/{user_id}/jobs/{job_id}/status",
            stream=True,
            timeout=30
        )
        
        for line in response.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                if line_str.startswith('data: '):
                    data = line_str[6:]  # Remove 'data: ' prefix
                    print(f"📨 SSE Event received: {data[:100]}...")
                    try:
                        event_data = json.loads(data)
                        print(f"   Parsed event: {json.dumps(event_data, indent=2)[:500]}")
                    except:
                        pass
    except Exception as e:
        print(f"❌ SSE Error: {e}")

def test_sync_with_sse():
    """Test synchronous job creation with SSE monitoring."""
    base_url = "http://localhost:8000"
    
    # Create session without proxy
    session = requests.Session()
    session.trust_env = False
    
    # First create a user
    email = f"test_{uuid.uuid4().hex[:8]}@example.com"
    password = "TestPassword123!"
    
    print(f"1️⃣ Creating user with email: {email}")
    
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
    print(f"✅ Created user: {user_id}")
    
    # Generate job ID upfront for SSE monitoring
    job_id = uuid.uuid4().hex
    
    # Start SSE listener in background thread
    sse_thread = threading.Thread(
        target=stream_sse_events, 
        args=(base_url, user_id, job_id, session)
    )
    sse_thread.daemon = True
    sse_thread.start()
    
    # Wait a moment for SSE to connect
    time.sleep(1)
    
    print(f"\n2️⃣ Creating job synchronously with ID: {job_id}")
    
    job_description = """
    Senior Software Engineer at TechCorp
    
    Requirements:
    - 5+ years of Python experience
    - Experience with FastAPI and SQLAlchemy
    - Strong knowledge of PostgreSQL
    - Experience with Redis and caching
    
    Responsibilities:
    - Design and implement backend services
    - Write clean, maintainable code
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
    
    if result.get("status") == "success":
        print(f"✅ Job created successfully: {result.get('job_id')}")
        
        # Wait for SSE events
        print("\n3️⃣ Waiting for SSE events...")
        time.sleep(5)
    else:
        print(f"❌ Job creation failed: {result.get('error')}")
    
    print("\n✅ Test complete!")

if __name__ == "__main__":
    test_sync_with_sse()