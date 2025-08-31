# Integration Tests for Job Endpoints

## Overview

These integration tests verify the job creation and SSE (Server-Sent Events) streaming functionality by testing against the actual running backend API.

## Prerequisites

Before running the tests, ensure:

1. **Backend services are running**:
   ```bash
   just up
   ```

2. **Services are accessible**:
   - Backend API: http://localhost:8000 (or http://127.0.0.1:8000)
   - Redis: localhost:6380
   - LiteLLM proxy: http://localhost:4000

3. **Important Notes**: 
   - The job creation endpoint requires a valid user in the database
   - Tests must create a user first via `/api/v1/auth/register` before creating jobs
   - User IDs must be valid UUIDs

4. **Proxy Issues (IMPORTANT)**:
   - If you have a system proxy configured (e.g., port 1082), it may interfere with httpx connections
   - The test scripts include `NO_PROXY=*` to bypass proxy for localhost
   - If tests fail with "Server disconnected without response", it's likely a proxy issue
   - Alternative: Use the `test_job_flow_requests.py` script which uses requests library and is more reliable

## Test Files

### `test_job_flow.py`
Main integration test file that tests:
- Job creation via POST endpoint
- SSE streaming connection and event reception
- Concurrent job creation
- Multiple clients streaming the same job
- Error handling scenarios

### `../scripts/test_job_streaming.py`
Flexible testing script with two modes:
- **Interactive mode**: Manual testing with real-time output
- **Automated mode**: CI/CD friendly with assertions and exit codes
- **Note**: Uses httpx, may have proxy issues

### `../scripts/test_job_streaming_with_auth.py`
Complete flow test that:
- Creates a user via registration
- Creates a job for that user
- Streams SSE events
- **Note**: Uses httpx, may have proxy issues

### `../scripts/test_job_flow_requests.py` (RECOMMENDED)
Reliable test using requests library:
- Works around proxy issues
- Creates user and job
- Streams SSE events
- More stable than httpx-based tests

## Running Tests

### Run All Integration Tests
```bash
# From project root
just backend-test

# Or directly with pytest
cd apps/backend
uv run pytest integration_tests/
```

### Run Specific Test
```bash
# Test a specific file
cd apps/backend
uv run pytest integration_tests/test_job_flow.py -v

# Test a specific test case
uv run pytest integration_tests/test_job_flow.py::TestJobEndpoints::test_create_job_and_stream_events -v
```

### Interactive Testing
```bash
# Manual interactive testing
just test-job-streaming

# With custom user ID
just test-job-streaming my-test-user
```

### Automated Testing (CI/CD)
```bash
# Run automated test with assertions
just test-job-streaming-automated

# Or directly
cd apps/backend
uv run python scripts/test_job_streaming.py --automated --timeout 30
```

## Test Flow

1. **Create Job**: POST to `/api/v1/users/{user_id}/jobs/create`
2. **Connect to SSE**: GET `/api/v1/users/{user_id}/jobs/{job_id}/status`
3. **Receive Events**: Listen for job processing events
4. **Verify Data**: Check that job data is extracted correctly

## What's Being Tested

### Functional Tests
- Job creation returns valid job_id
- SSE endpoint accepts connections
- Events are published to Redis and received via SSE
- Job data extraction works (title, company, skills, etc.)
- Multiple concurrent operations work correctly

### Non-Functional Tests
- SSE headers are correct for event streaming
- Timeouts are handled appropriately
- Invalid requests return proper error codes

## Debugging

If tests fail:

1. **Check services are running**:
   ```bash
   just ps
   ```

2. **Check logs**:
   ```bash
   just logs backend
   just logs litellm
   ```

3. **Run interactive test for detailed output**:
   ```bash
   cd apps/backend
   uv run python scripts/test_job_streaming.py
   ```

4. **Verify Redis connectivity**:
   ```bash
   redis-cli -p 6380 ping
   ```

## Notes

- Tests use real services (no mocks) to ensure end-to-end functionality
- Job processing may take 5-30 seconds depending on LLM response time
- Default timeout is 30 seconds for automated tests
- Each test run creates real data in the database