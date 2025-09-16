#!/usr/bin/env python3
"""
Reliable test script for job creation and SSE streaming using requests library.

This script works around proxy issues that affect httpx by using requests
with proxy disabled.

Usage:
    python scripts/test_job_flow_requests.py
"""

import os
# Disable all proxies
os.environ['NO_PROXY'] = '*'
os.environ['no_proxy'] = '*'

import sys
import time
import uuid
import json
import threading
from datetime import datetime

import requests


class JobFlowTester:
    def __init__(self, base_url="http://127.0.0.1:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.trust_env = False  # Ignore proxy settings
        
    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        print(f"[{timestamp}] [{level}] {message}")
        
    def create_user(self):
        """Create a test user and return user details."""
        email = f"test_{uuid.uuid4().hex[:8]}@example.com"
        password = "TestPassword123!"
        
        self.log(f"Creating user with email: {email}")
        
        response = self.session.post(
            f"{self.base_url}/api/v1/auth/register",
            json={
                "email": email,
                "password": password,
                "first_name": "Test",
                "last_name": "User"
            }
        )
        
        if response.status_code == 201:
            data = response.json()
            user_id = data.get('id')
            self.log(f"✓ User created: {user_id}", "SUCCESS")
            return user_id, email, password
        else:
            self.log(f"✗ Failed to create user: {response.status_code} - {response.text}", "ERROR")
            return None, None, None
            
    def create_job(self, user_id):
        """Create a job for the user."""
        self.log(f"Creating job for user: {user_id}")
        
        job_description = """
        Senior Software Engineer - Backend
        
        We are looking for an experienced Backend Engineer to join our team.
        
        Requirements:
        - 5+ years of Python experience
        - FastAPI expertise
        - PostgreSQL and Redis knowledge
        - Docker and Kubernetes experience
        
        Benefits:
        - Competitive salary
        - Remote work
        - Health insurance
        """
        
        response = self.session.post(
            f"{self.base_url}/api/v1/users/{user_id}/jobs/create",
            json={
                "job_description": job_description,
                "job_url": "https://example.com/jobs/senior-engineer"
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            job_id = data.get('job_id')
            self.log(f"✓ Job created: {job_id}", "SUCCESS")
            return job_id
        else:
            self.log(f"✗ Failed to create job: {response.status_code} - {response.text}", "ERROR")
            return None
            
    def stream_job_events(self, user_id, job_id, timeout=30):
        """Stream SSE events for the job."""
        url = f"{self.base_url}/api/v1/users/{user_id}/jobs/{job_id}/status"
        self.log(f"Connecting to SSE stream: {url}")
        
        events_received = []
        job_completed = False
        
        def stream_reader():
            nonlocal job_completed, events_received
            
            try:
                # Use stream=True for SSE
                response = self.session.get(url, stream=True, timeout=timeout)
                
                if response.status_code != 200:
                    self.log(f"✗ Failed to connect: {response.status_code}", "ERROR")
                    return
                    
                self.log("✓ Connected to SSE stream", "SUCCESS")
                self.log(f"Waiting for events (max {timeout}s)...")
                
                # Read the stream line by line
                for line in response.iter_lines():
                    if line:
                        line_str = line.decode('utf-8')
                        if line_str.startswith('data: '):
                            event_data = line_str[6:]  # Remove "data: " prefix
                            events_received.append(event_data)
                            
                            try:
                                data = json.loads(event_data)
                                
                                if isinstance(data, dict):
                                    if "title" in data:
                                        self.log("Job extracted successfully!", "SUCCESS")
                                        self.log(f"  Title: {data.get('title')}", "INFO")
                                        self.log(f"  Company: {data.get('company_name', 'N/A')}", "INFO")
                                        if data.get('skills'):
                                            self.log(f"  Skills: {', '.join(data['skills'][:5])}", "INFO")
                                        job_completed = True
                                        return
                                    else:
                                        self.log(f"Event received: {json.dumps(data, indent=2)}", "EVENT")
                                        
                            except json.JSONDecodeError:
                                self.log(f"Raw event: {event_data}", "EVENT")
                                
            except requests.Timeout:
                self.log(f"Stream timeout after {timeout}s", "WARNING")
            except Exception as e:
                self.log(f"Stream error: {e}", "ERROR")
                
        # Run the stream reader in a thread with timeout
        thread = threading.Thread(target=stream_reader)
        thread.daemon = True
        thread.start()
        thread.join(timeout=timeout)
        
        if thread.is_alive():
            self.log("Stream timeout - stopping", "WARNING")
            
        return job_completed, events_received
        
    def run_test(self):
        """Run the complete test flow."""
        self.log("="*60)
        self.log("Job Creation and SSE Streaming Test (Requests Library)")
        self.log("="*60)
        
        # Step 1: Create user
        user_id, email, password = self.create_user()
        if not user_id:
            self.log("❌ Test failed: Could not create user", "ERROR")
            return False
            
        # Step 2: Create job
        job_id = self.create_job(user_id)
        if not job_id:
            self.log("❌ Test failed: Could not create job", "ERROR")
            return False
            
        # Small delay for background processing
        time.sleep(1)
        
        # Step 3: Stream events
        job_completed, events = self.stream_job_events(user_id, job_id)
        
        self.log("="*60)
        if job_completed:
            self.log(f"✅ Test PASSED! Received {len(events)} events", "SUCCESS")
            self.log(f"User ID: {user_id}")
            self.log(f"Job ID: {job_id}")
            return True
        else:
            self.log("❌ Test FAILED! Job did not complete", "ERROR")
            self.log(f"Events received: {len(events)}")
            return False


def main():
    tester = JobFlowTester()
    success = tester.run_test()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()