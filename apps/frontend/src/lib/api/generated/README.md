# Generated API SDK

This directory contains the auto-generated TypeScript SDK for the Resume Genius API.

## Files

- `api.ts` - Typed axios client functions for all API endpoints
- `api.zod.ts` - Zod schemas for runtime validation
- `schemas/` - TypeScript interfaces for all API models
- `axios-instance.ts` - Custom axios instance with interceptors

## Usage

### Basic API Calls

```typescript
import * as api from '@/lib/api/generated/api';

// Register a new user
const user = await api.registerApiV1AuthRegisterPost({
  email: 'user@example.com',
  password: 'securepassword',
  first_name: 'John',
  last_name: 'Doe'
});

// Login
const tokens = await api.loginApiV1AuthLoginPost({
  email: 'user@example.com',
  password: 'securepassword'
});

// Get current user (add auth to axios instance first)
const currentUser = await api.getMeApiV1AuthMeGet();

// Create a job
const job = await api.createJobApiV1UsersUserIdJobsCreatePost(
  userId,
  {
    job_description: 'Software Engineer position...',
    job_url: 'https://example.com/job'
  }
);
```

### With Zod Validation

```typescript
import * as api from '@/lib/api/generated/api';
import * as schemas from '@/lib/api/generated/api.zod';

// Validate input before sending
const loginData = {
  email: 'user@example.com',
  password: 'password123'
};

// Validate with Zod schema
const validatedData = schemas.loginApiV1AuthLoginPostBody.parse(loginData);

// Make the API call
const response = await api.loginApiV1AuthLoginPost(validatedData);
```

### Authentication

Configure the axios instance to include auth tokens:

```typescript
// In axios-instance.ts, uncomment and modify the request interceptor:
axiosInstance.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);
```

### Error Handling

The axios instance includes error interceptors:

```typescript
try {
  const user = await api.getMeApiV1AuthMeGet();
} catch (error) {
  if (axios.isAxiosError(error)) {
    if (error.response?.status === 401) {
      // Handle unauthorized - redirect to login
    } else if (error.response?.status === 400) {
      // Handle validation error
      console.error('Validation error:', error.response.data);
    }
  }
}
```

### Type Safety

All functions are fully typed with TypeScript:

```typescript
import type { 
  UserResponse, 
  UserLoginRequest,
  UserLoginResponse 
} from '@/lib/api/generated/schemas';

// Types are automatically inferred
const login = async (credentials: UserLoginRequest): Promise<UserLoginResponse> => {
  return await api.loginApiV1AuthLoginPost(credentials);
};
```

### SSE Streaming (for job status)

For Server-Sent Events, you'll need to implement SSE separately as axios doesn't support streaming:

```typescript
const eventSource = new EventSource(
  `${process.env.NEXT_PUBLIC_API_URL}/api/v1/users/${userId}/jobs/${jobId}/status`
);

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Job status update:', data);
};

eventSource.onerror = (error) => {
  console.error('SSE error:', error);
  eventSource.close();
};
```

## Regenerating the SDK

To regenerate the SDK after backend API changes:

```bash
just generate-sdk
```

This will:
1. Export the OpenAPI schema from the backend
2. Generate new axios client functions
3. Generate new Zod schemas
4. Update TypeScript types

The generation is fully automated - no manual changes needed!