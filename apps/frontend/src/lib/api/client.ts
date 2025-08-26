import { z } from "zod";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
    public data?: unknown
  ) {
    super(message);
    this.name = "ApiError";
  }
}

interface RequestOptions extends RequestInit {
  params?: Record<string, string | number | boolean>;
}

export async function apiClient<T>(
  endpoint: string,
  schema: z.ZodSchema<T>,
  options: RequestOptions = {}
): Promise<T> {
  const { params, ...fetchOptions } = options;

  let url = `${API_BASE_URL}${endpoint}`;
  
  if (params) {
    const searchParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      searchParams.append(key, String(value));
    });
    url = `${url}?${searchParams.toString()}`;
  }

  const response = await fetch(url, {
    ...fetchOptions,
    headers: {
      "Content-Type": "application/json",
      ...fetchOptions.headers,
    },
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => null);
    throw new ApiError(
      response.status,
      errorData?.message || `API Error: ${response.statusText}`,
      errorData
    );
  }

  const data = await response.json();
  
  try {
    return schema.parse(data);
  } catch (error) {
    if (error instanceof z.ZodError) {
      console.error("Schema validation failed:", error.issues);
      throw new ApiError(500, "Invalid API response format", error.issues);
    }
    throw error;
  }
}

export const api = {
  get: <T>(endpoint: string, schema: z.ZodSchema<T>, options?: RequestOptions) =>
    apiClient(endpoint, schema, { ...options, method: "GET" }),
  
  post: <T>(endpoint: string, schema: z.ZodSchema<T>, body?: unknown, options?: RequestOptions) =>
    apiClient(endpoint, schema, {
      ...options,
      method: "POST",
      body: body ? JSON.stringify(body) : undefined,
    }),
  
  put: <T>(endpoint: string, schema: z.ZodSchema<T>, body?: unknown, options?: RequestOptions) =>
    apiClient(endpoint, schema, {
      ...options,
      method: "PUT",
      body: body ? JSON.stringify(body) : undefined,
    }),
  
  delete: <T>(endpoint: string, schema: z.ZodSchema<T>, options?: RequestOptions) =>
    apiClient(endpoint, schema, { ...options, method: "DELETE" }),
};