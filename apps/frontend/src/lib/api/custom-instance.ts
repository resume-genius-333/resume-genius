import { z } from 'zod';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
    public data?: unknown
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

interface CustomInstanceConfig<T> {
  url: string;
  method: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH';
  params?: any;
  data?: any;
  headers?: Record<string, string>;
  responseSchema?: z.ZodSchema<T>;
}

/**
 * Custom instance for Orval that integrates with our existing API client pattern
 * and provides Zod schema validation for responses
 */
export const customInstance = async <T>({
  url,
  method,
  params,
  data,
  headers,
  responseSchema,
}: CustomInstanceConfig<T>): Promise<T> => {
  // Build the full URL
  let fullUrl = `${API_BASE_URL}${url}`;
  
  // Add query parameters if present
  if (params) {
    const searchParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        searchParams.append(key, String(value));
      }
    });
    const queryString = searchParams.toString();
    if (queryString) {
      fullUrl = `${fullUrl}?${queryString}`;
    }
  }

  // Prepare fetch options
  const fetchOptions: RequestInit = {
    method,
    headers: {
      'Content-Type': 'application/json',
      ...headers,
    },
  };

  // Add body for POST, PUT, PATCH requests
  if (data && ['POST', 'PUT', 'PATCH'].includes(method)) {
    fetchOptions.body = JSON.stringify(data);
  }

  try {
    // Make the request
    const response = await fetch(fullUrl, fetchOptions);

    // Handle non-OK responses
    if (!response.ok) {
      const errorData = await response.json().catch(() => null);
      throw new ApiError(
        response.status,
        errorData?.detail || errorData?.message || `API Error: ${response.statusText}`,
        errorData
      );
    }

    // Handle empty responses (204 No Content, etc.)
    if (response.status === 204 || response.headers.get('content-length') === '0') {
      return undefined as any;
    }

    // Parse JSON response
    const responseData = await response.json();

    // If a response schema is provided, validate the response
    if (responseSchema) {
      try {
        return responseSchema.parse(responseData);
      } catch (error) {
        if (error instanceof z.ZodError) {
          console.error('Response validation failed:', error.issues);
          throw new ApiError(500, 'Invalid API response format', error.issues);
        }
        throw error;
      }
    }

    return responseData;
  } catch (error) {
    // Re-throw ApiError instances
    if (error instanceof ApiError) {
      throw error;
    }
    
    // Handle network errors
    if (error instanceof Error) {
      throw new ApiError(0, `Network error: ${error.message}`, error);
    }
    
    throw new ApiError(0, 'Unknown error occurred', error);
  }
};

export type ErrorType<T = any> = ApiError;