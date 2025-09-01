#!/usr/bin/env python3
"""Simple test to verify SSE streaming works."""

import os
import requests
import uuid
import json
import time
import threading

# Bypass proxy
os.environ['NO_PROXY'] = '*'

def test_sse():
    base_url = "http://localhost:8000"
    session = requests.Session()
    session.trust_env = False
    
    # Create a user first
    email = f"test_{uuid.uuid4().hex[:8]}@example.com"
    response = session.post(
        f"{base_url}/api/v1/auth/register",
        json={
            "email": email,
            "password": "TestPassword123!",
            "first_name": "Test",
            "last_name": "User"
        }
    )
    
    user_data = response.json()
    user_id = user_data.get("id")
    print(f"Created user: {user_id}")
    
    # Create a job
    response = session.post(
        f"{base_url}/api/v1/users/{user_id}/jobs/create",
        json={
            "job_description": "Test job for SSE",
            "job_url": "https://example.com/job"
        }
    )
    
    job_data = response.json()
    job_id = job_data.get("job_id")
    print(f"Created job: {job_id}")
    
    # Wait a bit for background task to complete
    print("Waiting 3 seconds for background task...")
    time.sleep(3)
    
    # Now try to connect to SSE
    print(f"\nConnecting to SSE: /api/v1/users/{user_id}/jobs/{job_id}/status")
    
    def stream_reader():
        try:
            resp = session.get(
                f"{base_url}/api/v1/users/{user_id}/jobs/{job_id}/status",
                stream=True,
                timeout=10
            )
            print(f"SSE Response status: {resp.status_code}")
            print(f"SSE Response headers: {resp.headers}")
            
            for line in resp.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    print(f"Received line: {line_str}")
                    if line_str.startswith('data: '):
                        data = line_str[6:]
                        print(f"Event data: {data[:200]}...")
                        try:
                            parsed = json.loads(data)
                            print(f"Parsed JSON: {json.dumps(parsed, indent=2)[:500]}")
                        except:
                            pass
        except Exception as e:
            print(f"SSE Error: {e}")
    
    # Start SSE reader in thread
    thread = threading.Thread(target=stream_reader)
    thread.daemon = True
    thread.start()
    
    # Wait for thread to complete
    thread.join(timeout=15)
    print("\nTest complete!")

if __name__ == "__main__":
    test_sse()