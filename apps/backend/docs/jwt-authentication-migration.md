# JWT Authentication Migration Guide

## Overview
This document outlines the migration from URL-based user identification to JWT-based authentication for the jobs API endpoints.

## Current Implementation
Currently, the jobs router uses `user_id` as a path parameter:
- `/users/{user_id}/jobs/create`
- `/users/{user_id}/jobs/{job_id}/select_relevant_info`
- `/users/{user_id}/jobs/{job_id}/refine`
- `/users/{user_id}/jobs/{job_id}/status-stream`
- `/users/{user_id}/jobs/{job_id}/status`

## Target Implementation
Remove `user_id` from paths and use JWT authentication to identify users:
- `/jobs/create`
- `/jobs/{job_id}/select_relevant_info`
- `/jobs/{job_id}/refine`
- `/jobs/{job_id}/status-stream`
- `/jobs/{job_id}/status`

## Implementation Steps

### 1. Update Imports
Add the following import to `jobs.py`:
```python
from src.api.dependencies import get_current_active_user
from src.models.auth import UserResponse
```

### 2. Modify Route Handlers

#### Create Job Endpoint
**Before:**
```python
@router.post("/users/{user_id}/jobs/create", response_model=CreateJobResponse)
async def create_job(
    user_id: uuid.UUID,
    input_body: CreateJobRequest,
    background_tasks: BackgroundTasks,
):
    job_id = uuid.uuid4()
    background_tasks.add_task(
        _create_job_background_wrapper, user_id, job_id, input_body
    )
    return CreateJobResponse(
        job_id=job_id,
        sse_url=f"http://localhost:8000/api/v1/users/{user_id}/jobs/{job_id}/status",
    )
```

**After:**
```python
@router.post("/jobs/create", response_model=CreateJobResponse)
async def create_job(
    input_body: CreateJobRequest,
    background_tasks: BackgroundTasks,
    current_user: UserResponse = Depends(get_current_active_user),
):
    user_id = uuid.UUID(current_user.id)
    job_id = uuid.uuid4()
    background_tasks.add_task(
        _create_job_background_wrapper, user_id, job_id, input_body
    )
    return CreateJobResponse(
        job_id=job_id,
        sse_url=f"http://localhost:8000/api/v1/jobs/{job_id}/status",
    )
```

#### Select Relevant Info Endpoint
**Before:**
```python
@router.post("/users/{user_id}/jobs/{job_id}/select_relevant_info")
async def select_relevant_info(user_id: uuid.UUID, job_id: uuid.UUID):
    pass
```

**After:**
```python
@router.post("/jobs/{job_id}/select_relevant_info")
async def select_relevant_info(
    job_id: uuid.UUID,
    current_user: UserResponse = Depends(get_current_active_user),
):
    user_id = uuid.UUID(current_user.id)
    # Implementation continues with user_id available
    pass
```

#### Refine Resume Endpoint
**Before:**
```python
@router.post("/users/{user_id}/jobs/{job_id}/refine")
async def refine_resume(
    user_id: uuid.UUID,
    job_id: uuid.UUID,
):
    return {"status": "success", "message": "Resume refinement started"}
```

**After:**
```python
@router.post("/jobs/{job_id}/refine")
async def refine_resume(
    job_id: uuid.UUID,
    current_user: UserResponse = Depends(get_current_active_user),
):
    user_id = uuid.UUID(current_user.id)
    return {"status": "success", "message": "Resume refinement started"}
```

#### Stream Status Endpoint
**Before:**
```python
@router.get("/users/{user_id}/jobs/{job_id}/status-stream")
async def stream_status(
    user_id: uuid.UUID,
    job_id: uuid.UUID,
):
    return StreamingResponse(
        _stream_status(user_id, job_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
```

**After:**
```python
@router.get("/jobs/{job_id}/status-stream")
async def stream_status(
    job_id: uuid.UUID,
    current_user: UserResponse = Depends(get_current_active_user),
):
    user_id = uuid.UUID(current_user.id)
    return StreamingResponse(
        _stream_status(user_id, job_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
```

#### Get Status Endpoint
**Before:**
```python
@router.get("/users/{user_id}/jobs/{job_id}/status", response_model=ProcessingStatus)
async def get_status(
    user_id: uuid.UUID,
    job_id: uuid.UUID,
):
    return await get_processing_status(user_id, job_id)
```

**After:**
```python
@router.get("/jobs/{job_id}/status", response_model=ProcessingStatus)
async def get_status(
    job_id: uuid.UUID,
    current_user: UserResponse = Depends(get_current_active_user),
):
    user_id = uuid.UUID(current_user.id)
    return await get_processing_status(user_id, job_id)
```

## Benefits of This Approach

1. **Security**: User ID is extracted from the authenticated JWT token, preventing users from accessing other users' resources
2. **RESTful Design**: Cleaner URLs that don't expose internal user IDs
3. **Consistency**: Follows the same pattern as other authenticated endpoints (e.g., `/auth/me`)
4. **Simplified Client Code**: Clients don't need to manage user IDs in URLs

## Authentication Flow

1. Client authenticates via `/auth/login` and receives JWT tokens
2. Client includes the access token in the `Authorization: Bearer <token>` header
3. The `get_current_active_user` dependency:
   - Validates the JWT token
   - Checks if the token is blacklisted
   - Verifies token expiration
   - Ensures the user is active
   - Returns the authenticated user's information
4. The endpoint extracts the user ID from the authenticated user object

## Testing

After implementing these changes:

1. Ensure all endpoints require authentication:
   ```bash
   # This should return 401 Unauthorized
   curl -X POST http://localhost:8000/api/v1/jobs/create \
     -H "Content-Type: application/json" \
     -d '{"job_description": "Test job"}'
   ```

2. Test with valid authentication:
   ```bash
   # First, login to get token
   TOKEN=$(curl -X POST http://localhost:8000/api/v1/auth/login \
     -H "Content-Type: application/json" \
     -d '{"email": "user@example.com", "password": "password"}' \
     | jq -r '.access_token')
   
   # Then use token to create job
   curl -X POST http://localhost:8000/api/v1/jobs/create \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer $TOKEN" \
     -d '{"job_description": "Test job"}'
   ```

## Migration Checklist

- [ ] Update all route paths to remove `/users/{user_id}` prefix
- [ ] Add `get_current_active_user` dependency to all endpoints
- [ ] Update function signatures to accept `current_user` parameter
- [ ] Extract `user_id` from `current_user.id` where needed
- [ ] Update any hardcoded URLs in responses (e.g., SSE URLs)
- [ ] Update API documentation/OpenAPI schema
- [ ] Update frontend to use new endpoints
- [ ] Test all endpoints with and without authentication
- [ ] Verify users can only access their own resources

## Frontend Updates Required

The frontend will need to:
1. Remove user ID from API calls
2. Update endpoint URLs
3. Ensure JWT token is included in all requests to protected endpoints

Example:
```typescript
// Before
const response = await fetch(`/api/v1/users/${userId}/jobs/create`, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify(jobData),
});

// After
const response = await fetch('/api/v1/jobs/create', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${accessToken}`,
  },
  body: JSON.stringify(jobData),
});
```