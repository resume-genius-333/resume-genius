#!/usr/bin/env python3
"""Test the full flow with debugging."""

import os
import requests
import uuid
import json
import time
import threading
import asyncio
import redis.asyncio as redis

# Bypass proxy
os.environ['NO_PROXY'] = '*'

def test_full_flow():
    base_url = "http://localhost:8000"
    session = requests.Session()
    session.trust_env = False
    
    # Create a user
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
            "job_description": "Test job for full flow",
            "job_url": "https://example.com/job"
        }
    )
    
    job_data = response.json()
    job_id = job_data.get("job_id")
    print(f"Created job: {job_id}")
    print(f"Job response: {job_data}")
    
    # Start SSE listener
    print(f"\n1. Starting SSE listener for channel...")
    sse_url = f"{base_url}/api/v1/users/{user_id}/jobs/{job_id}/status"
    print(f"   SSE URL: {sse_url}")
    
    received_events = []
    
    def sse_listener():
        try:
            resp = session.get(sse_url, stream=True, timeout=30)
            print(f"   SSE connected: {resp.status_code}")
            
            for line in resp.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    print(f"   SSE received: {line_str[:100]}...")
                    received_events.append(line_str)
                    if line_str.startswith('data: '):
                        data = line_str[6:]
                        try:
                            parsed = json.loads(data)
                            print(f"   Parsed event: {json.dumps(parsed, indent=2)[:200]}...")
                        except:
                            pass
        except Exception as e:
            print(f"   SSE error: {e}")
    
    thread = threading.Thread(target=sse_listener)
    thread.daemon = True
    thread.start()
    
    # Wait for SSE to connect
    time.sleep(2)
    
    # Check what channel the backend published to
    print(f"\n2. Checking backend logs for this job...")
    # This would need to be done via docker logs
    
    # Manually publish to test
    print(f"\n3. Manually publishing to Redis channel...")
    
    async def manual_publish():
        r = await redis.from_url("redis://localhost:6380")
        
        # Try the exact channel format the backend uses
        channel = f"user:{user_id.replace('-', '')}:job:{job_id}"
        print(f"   Publishing to channel: {channel}")
        
        test_msg = json.dumps({
            "id": job_id,
            "user_id": user_id,
            "status": "manual_test",
            "message": "Manual test message"
        })
        
        result = await r.publish(channel, test_msg)
        print(f"   Publish result: {result} subscribers")
        
        await r.aclose()
    
    asyncio.run(manual_publish())
    
    # Wait for events
    print(f"\n4. Waiting 5 seconds for events...")
    time.sleep(5)
    
    print(f"\n5. Results:")
    print(f"   Events received: {len(received_events)}")
    for event in received_events:
        print(f"   - {event[:100]}...")
    
    thread.join(timeout=1)
    print("\nTest complete!")

if __name__ == "__main__":
    test_full_flow()