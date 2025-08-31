"""
Integration tests for job creation and SSE streaming.

Prerequisites:
- Backend must be running at http://localhost:8000
- Redis must be accessible
- LiteLLM must be configured

Run with: pytest integration_tests/test_job_flow.py -v
"""

import asyncio
import json
import pytest
import httpx
from datetime import datetime


class TestJobEndpoints:
    """Test the complete job creation and streaming flow."""
    
    @pytest.mark.asyncio
    async def test_create_job_and_stream_events(
        self, 
        api_client: httpx.AsyncClient,
        test_user_id: str,
        sample_job_description: str
    ):
        """
        Test the complete flow:
        1. Create a job via POST endpoint
        2. Connect to SSE stream
        3. Verify events are received
        """
        
        print(f"\n[{datetime.now().isoformat()}] Starting integration test")
        print(f"User ID: {test_user_id}")
        
        # Step 1: Create a job
        print("\n1. Creating job...")
        create_response = await api_client.post(
            f"/api/v1/users/{test_user_id}/jobs/create",
            json={
                "job_description": sample_job_description,
                "job_url": "https://example.com/job/123"
            }
        )
        
        assert create_response.status_code == 200, f"Failed to create job: {create_response.text}"
        job_data = create_response.json()
        assert "job_id" in job_data, "Response missing job_id"
        job_id = job_data["job_id"]
        print(f"✓ Job created with ID: {job_id}")
        
        # Step 2: Connect to SSE stream and wait for events
        print("\n2. Connecting to SSE stream...")
        stream_url = f"/api/v1/users/{test_user_id}/jobs/{job_id}/status"
        
        received_events = []
        stream_timeout = 30  # Maximum time to wait for events
        
        try:
            # Use asyncio timeout for the entire streaming operation
            async with asyncio.timeout(stream_timeout):
                async with api_client.stream("GET", stream_url) as response:
                    assert response.status_code == 200, f"Failed to connect to stream: {response.status_code}"
                    print("✓ Connected to SSE stream")
                    
                    # Check headers
                    assert response.headers.get("content-type", "").startswith("text/event-stream"), \
                        "Invalid content-type for SSE"
                    
                    print(f"\n3. Waiting for events (max {stream_timeout}s)...")
                    
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            event_data = line[6:]  # Remove "data: " prefix
                            print(f"   Received event: {event_data[:100]}...")
                            
                            # Try to parse as JSON
                            try:
                                parsed_event = json.loads(event_data)
                                received_events.append(parsed_event)
                                
                                # Check if this is the job completion event
                                if isinstance(parsed_event, dict):
                                    if "title" in parsed_event:
                                        print(f"   ✓ Job extracted - Title: {parsed_event.get('title')}")
                                        break  # We got the job data, test successful
                                        
                            except json.JSONDecodeError:
                                print(f"   Warning: Could not parse event as JSON: {event_data}")
                    
        except asyncio.TimeoutError:
            print(f"\n⚠ Timeout after {stream_timeout}s - no job completion event received")
            print(f"   Events received: {len(received_events)}")
            if not received_events:
                pytest.fail(f"No events received within {stream_timeout} seconds")
        
        # Step 3: Verify we received valid job data
        print("\n4. Verifying received data...")
        assert len(received_events) > 0, "No events were received"
        
        # Find the job data event (should contain extracted job information)
        job_event = None
        for event in received_events:
            if isinstance(event, dict) and "title" in event:
                job_event = event
                break
        
        assert job_event is not None, f"No job completion event found in {len(received_events)} events"
        
        # Verify job data structure
        assert "title" in job_event, "Job event missing title"
        assert job_event["title"], "Job title is empty"
        print(f"✓ Job title: {job_event['title']}")
        
        if "company_name" in job_event:
            print(f"✓ Company: {job_event['company_name']}")
        
        if "skills" in job_event and job_event["skills"]:
            print(f"✓ Skills extracted: {', '.join(job_event['skills'][:5])}")
        
        print("\n✅ Integration test completed successfully!")
        print(f"   Total events received: {len(received_events)}")
        
        return job_id, received_events
    
    @pytest.mark.asyncio
    async def test_concurrent_job_creation(
        self,
        api_client: httpx.AsyncClient,
        test_user_id: str,
        sample_job_description: str
    ):
        """Test creating multiple jobs concurrently."""
        
        print(f"\n[{datetime.now().isoformat()}] Testing concurrent job creation")
        
        # Create 3 jobs concurrently
        tasks = []
        for i in range(3):
            task = api_client.post(
                f"/api/v1/users/{test_user_id}/jobs/create",
                json={
                    "job_description": f"Job {i+1}: {sample_job_description}",
                    "job_url": f"https://example.com/job/{i+1}"
                }
            )
            tasks.append(task)
        
        print("Creating 3 jobs concurrently...")
        responses = await asyncio.gather(*tasks)
        
        # Verify all succeeded
        job_ids = []
        for i, response in enumerate(responses):
            assert response.status_code == 200, f"Job {i+1} failed: {response.text}"
            job_data = response.json()
            assert "job_id" in job_data
            job_ids.append(job_data["job_id"])
            print(f"✓ Job {i+1} created: {job_data['job_id']}")
        
        # Verify all job IDs are unique
        assert len(job_ids) == len(set(job_ids)), "Duplicate job IDs generated"
        
        print(f"\n✅ Successfully created {len(job_ids)} concurrent jobs")
        return job_ids
    
    @pytest.mark.asyncio
    async def test_stream_multiple_clients(
        self,
        api_client: httpx.AsyncClient,
        test_user_id: str,
        sample_job_description: str
    ):
        """Test that multiple clients can stream the same job status."""
        
        print(f"\n[{datetime.now().isoformat()}] Testing multiple SSE clients")
        
        # First create a job
        create_response = await api_client.post(
            f"/api/v1/users/{test_user_id}/jobs/create",
            json={
                "job_description": sample_job_description,
                "job_url": "https://example.com/job/multi"
            }
        )
        
        assert create_response.status_code == 200
        job_id = create_response.json()["job_id"]
        print(f"✓ Job created: {job_id}")
        
        # Connect two clients to the same stream
        stream_url = f"/api/v1/users/{test_user_id}/jobs/{job_id}/status"
        
        async def stream_client(client_id: int):
            """Helper to stream events for a client."""
            events = []
            try:
                async with asyncio.timeout(15):
                    async with api_client.stream("GET", stream_url) as response:
                        print(f"  Client {client_id}: Connected")
                        async for line in response.aiter_lines():
                            if line.startswith("data: "):
                                event_data = line[6:]
                                try:
                                    parsed = json.loads(event_data)
                                    events.append(parsed)
                                    if isinstance(parsed, dict) and "title" in parsed:
                                        print(f"  Client {client_id}: Received job data")
                                        break
                                except json.JSONDecodeError:
                                    pass
            except asyncio.TimeoutError:
                print(f"  Client {client_id}: Timeout")
            
            return client_id, events
        
        print("\nConnecting 2 clients to the same job stream...")
        
        # Start both clients concurrently
        results = await asyncio.gather(
            stream_client(1),
            stream_client(2)
        )
        
        # Verify both clients received events
        for client_id, events in results:
            assert len(events) > 0, f"Client {client_id} received no events"
            print(f"✓ Client {client_id}: Received {len(events)} events")
        
        print("\n✅ Multiple clients successfully received events")


class TestErrorCases:
    """Test error handling scenarios."""
    
    @pytest.mark.asyncio
    async def test_invalid_job_request(self, api_client: httpx.AsyncClient, test_user_id: str):
        """Test that invalid requests are properly rejected."""
        
        print(f"\n[{datetime.now().isoformat()}] Testing error handling")
        
        # Test with missing required field
        response = await api_client.post(
            f"/api/v1/users/{test_user_id}/jobs/create",
            json={"invalid_field": "value"}
        )
        
        assert response.status_code == 422, "Should reject invalid request"
        print("✓ Invalid request properly rejected")
    
    @pytest.mark.asyncio
    async def test_stream_nonexistent_job(self, api_client: httpx.AsyncClient, test_user_id: str):
        """Test streaming for a job that doesn't exist."""
        
        import uuid
        fake_job_id = str(uuid.uuid4())
        stream_url = f"/api/v1/users/{test_user_id}/jobs/{fake_job_id}/status"
        
        # This should still connect (SSE doesn't fail on connection)
        # but won't receive any events
        received_events = []
        
        try:
            async with asyncio.timeout(5):
                async with api_client.stream("GET", stream_url) as response:
                    assert response.status_code == 200, "SSE should connect even for non-existent jobs"
                    
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            received_events.append(line[6:])
                            
        except asyncio.TimeoutError:
            pass  # Expected - no events for non-existent job
        
        # Should not receive any job data events
        assert len(received_events) == 0 or \
               not any("title" in event for event in received_events), \
               "Should not receive job data for non-existent job"
        
        print("✓ Non-existent job stream handled correctly")