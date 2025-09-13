import axios, { AxiosRequestConfig, ResponseType } from "axios";
import z, { ZodObject } from "zod";

// Use relative URL to go through Next.js proxy
const BACKEND_URL =
  process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

// Create axios instance with default config
const axiosInstance = axios.create({
  baseURL: BACKEND_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// Request interceptor for auth token and logging
axiosInstance.interceptors.request.use(
  (config) => {
    // Token is set in AuthContext when logging in or refreshing
    const token = localStorage.getItem("access_token");
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    // Detailed request logging
    console.group(
      `🚀 API Request: ${config.method?.toUpperCase()} ${config.url}`
    );
    console.log("Full URL:", `${config.baseURL}${config.url}`);
    console.log("Method:", config.method);
    console.log("Headers:", config.headers);
    console.log("Params:", config.params);
    console.log("Data:", config.data);
    console.log("Response Type:", config.responseType);
    console.log("Timestamp:", new Date().toISOString());
    console.groupEnd();

    return config;
  },
  (error) => {
    console.error("❌ Request Interceptor Error:", error);
    return Promise.reject(error);
  }
);

// Response interceptor for logging and error handling
axiosInstance.interceptors.response.use(
  (response) => {
    // Detailed response logging
    console.group(
      `✅ API Response: ${response.config.method?.toUpperCase()} ${response.config.url}`
    );
    console.log("Status:", response.status, response.statusText);
    console.log("Headers:", response.headers);
    console.log("Data:", response.data);
    console.log(
      "Duration:",
      `${Date.now() - (response.config as any).requestStartTime}ms`
    );
    console.log("Timestamp:", new Date().toISOString());
    console.groupEnd();

    return response;
  },
  (error) => {
    // Detailed error logging
    console.group(
      `❌ API Error: ${error.config?.method?.toUpperCase()} ${error.config?.url}`
    );
    console.error("Error Message:", error.message);
    console.error("Error Code:", error.code);

    if (error.response) {
      // Server responded with error
      console.error("Response Status:", error.response.status);
      console.error("Response Data:", error.response.data);
      console.error("Response Headers:", error.response.headers);
    } else if (error.request) {
      // Request made but no response
      console.error("No response received");
      console.error("Request:", error.request);
    } else {
      // Error in setting up request
      console.error("Request Setup Error:", error.message);
    }

    console.error("Config:", error.config);
    console.error("Timestamp:", new Date().toISOString());
    console.groupEnd();

    return Promise.reject(error);
  }
);

type MaybeZodObject<T> = T extends ZodObject ? z.output<T> : T;
type MaybeZodInput<T> = T extends ZodObject ? { responseSchema: T } : {};

type CustomAxiosRequestConfig<D = any> = Omit<
  AxiosRequestConfig<D>,
  "responseType"
> & {
  responseType?: "sse-stream" | ResponseType;
};

export function customAxiosInstance<T = any, D = any>(
  config: CustomAxiosRequestConfig<D> & {
    responseType: "sse-stream";
  } & MaybeZodInput<T>
): Promise<ReadableStream<MaybeZodObject<T>>>;

export function customAxiosInstance<T, D = any>(
  config: CustomAxiosRequestConfig<D> & MaybeZodInput<T>
): Promise<MaybeZodObject<T>>;

/**
 * Custom axios instance for Orval
 * This function is used by Orval to make API requests
 *
 * - if `responseType` is `sse-stream`, then we use Fetch API for true streaming support
 * - otherwise, we use axios for regular requests
 */
export async function customAxiosInstance<T = any, D = any>(
  config: CustomAxiosRequestConfig<D> & {
    responseSchema?: T;
  }
): Promise<MaybeZodObject<T> | ReadableStream<MaybeZodObject<T>>> {
  if (typeof window === "undefined") {
    console.log("Not in browser");
  } else {
    console.log("In browser");
  }
  const isSseStreaming = config.responseType === "sse-stream";

  // Use Fetch API for SSE streaming
  if (isSseStreaming) {
    return handleSSEWithFetch(config);
  }

  // Use axios for non-streaming requests
  const params: AxiosRequestConfig<D> = {
    ...config,
    // Add timestamp for duration calculation
    ...({
      requestStartTime: Date.now(),
    } as any),
  };

  // Log custom axios instance request
  console.log(
    `🔧 Custom Axios Instance: ${config.method || "GET"} ${config.url}`,
    {
      isSSE: false,
      responseType: config.responseType,
      hasSchema: !!config.responseSchema,
    }
  );

  const response = await axiosInstance(params);

  // Handle non-streaming response
  const responseData = response.data;

  // Apply Zod validation if schema provided
  if (config.responseSchema) {
    return (config.responseSchema as any).parse(responseData);
  }

  return responseData;
}

/**
 * Handle SSE streaming using Fetch API
 */
async function handleSSEWithFetch<T = any, D = any>(
  config: CustomAxiosRequestConfig<D> & {
    responseSchema?: T;
  }
): Promise<ReadableStream<MaybeZodObject<T>>> {
  // Construct full URL
  // Safer join of BACKEND_URL and config.url
  const fullUrl = [
    BACKEND_URL.replace(/\/+$/, ""),
    String(config.url).replace(/^\/+/, ""),
  ].join("/");

  // Get auth token
  const token = localStorage.getItem("access_token");

  // Prepare headers
  const headers: Record<string, string> = {
    Accept: "text/event-stream",
    "Cache-Control": "no-cache",
    "X-Accel-Buffering": "no", // Disable proxy buffering
    ...((config.headers as any) || {}),
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  // Log the fetch request
  const requestStartTime = Date.now();
  console.group(
    `🚀 Fetch API Request (SSE): ${config.method || "GET"} ${config.url}`
  );
  console.log("Full URL:", fullUrl);
  console.log("Method:", config.method || "GET");
  console.log("Headers:", headers);
  console.log("Data:", config.data);
  console.log("Timestamp:", new Date().toISOString());
  console.groupEnd();

  try {
    // Make the fetch request
    const response = await fetch(fullUrl, {
      method: config.method?.toUpperCase() || "GET",
      headers,
      body: config.data ? JSON.stringify(config.data) : undefined,
      signal: config.signal as AbortSignal | undefined,
    });

    // Log response
    console.group(
      `✅ Fetch API Response (SSE): ${config.method || "GET"} ${config.url}`
    );
    console.log("Status:", response.status, response.statusText);
    // Log headers in a compatible way
    const headersObj: Record<string, string> = {};
    response.headers.forEach((value, key) => {
      headersObj[key] = value;
    });
    console.log("Headers:", headersObj);
    console.log("Duration:", `${Date.now() - requestStartTime}ms`);
    console.log("Timestamp:", new Date().toISOString());
    console.groupEnd();

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    if (!response.body) {
      throw new Error("Response body is null");
    }

    // Convert the response body to SSE stream
    return convertFetchStreamToSSE(
      response.body,
      config.responseSchema,
      config.url
    );
  } catch (error) {
    console.group(
      `❌ Fetch API Error (SSE): ${config.method || "GET"} ${config.url}`
    );
    console.error("Error:", error);
    console.error("Duration:", `${Date.now() - requestStartTime}ms`);
    console.error("Timestamp:", new Date().toISOString());
    console.groupEnd();
    throw error;
  }
}

/**
 * Convert Fetch API ReadableStream to SSE event stream with Zod validation
 */
function convertFetchStreamToSSE<T = any>(
  body: ReadableStream<Uint8Array>,
  responseSchema?: T,
  url?: string
): ReadableStream<MaybeZodObject<T>> {
  const decoder = new TextDecoder();
  let buffer = "";
  let eventCount = 0;
  const streamStartTime = Date.now();

  console.log(`🌊 SSE Stream initialized for: ${url || "unknown"}`);
  const reader = body.getReader();

  return new ReadableStream<MaybeZodObject<T>>({
    async start(controller) {
      console.log(`🔍 SSE Stream reader created for ${url || "stream"}`);
    },
    async pull(controller) {
      console.group("SSE Stream pull");
      try {
        console.log(`⏳ Waiting for next chunk from ${url || "stream"}...`);
        const { done, value } = await reader.read();

        if (done) {
          console.log(`🏁 Stream done signal received for ${url || "stream"}`);
          // Process any remaining buffer
          if (buffer.trim()) {
            console.log(`📝 Processing remaining buffer:`, buffer);
            processSSEBuffer(
              buffer,
              controller,
              responseSchema,
              eventCount,
              url
            );
          }

          const duration = Date.now() - streamStartTime;
          console.log(`✅ SSE Stream completed for ${url || "stream"}:`, {
            totalEvents: eventCount,
            duration: `${duration}ms`,
          });

          reader.releaseLock();
          controller.close();
          return;
        }

        // Decode the chunk and add to buffer
        const chunk = decoder.decode(value, { stream: true });
        buffer += chunk;

        console.log(`📦 SSE Chunk received for ${url || "stream"}:`, {
          size: `${value?.length} bytes`,
          bufferSize: `${buffer.length} bytes`,
          chunkPreview: chunk.substring(0, 200),
          rawChunk: chunk,
        });

        // Process complete SSE events (separated by double newlines)
        const events = buffer.split("\n\n");
        // Keep the last (potentially incomplete) event in the buffer
        buffer = events.pop() || "";

        console.log(`🔄 Processing ${events.length} complete events`);
        for (const event of events) {
          if (!event.trim()) continue;
          console.log(`📋 Processing event:`, event);

          const result = parseSSEEvent(event);
          if (result) {
            eventCount++;
            processSSEData(result, controller, responseSchema, eventCount, url);
          }
        }
      } catch (error) {
        console.error(`❌ SSE Stream error for ${url || "stream"}:`, error, {
          eventsProcessed: eventCount,
          duration: `${Date.now() - streamStartTime}ms`,
          buffer: buffer,
        });
        reader.releaseLock();
        controller.error(error);
      } finally {
      }
      console.groupEnd();
    },
    cancel() {
      console.log(`🛑 SSE Stream cancelled for ${url || "stream"}`);
      reader.releaseLock();
      body.cancel();
    },
  });
}

/**
 * Parse an SSE event from text
 */
function parseSSEEvent(event: string): string | null {
  const lines = event.split("\n");
  let eventData = "";

  for (const line of lines) {
    if (line.startsWith("data: ")) {
      // Extract data after "data: " prefix
      const dataContent = line.slice(6);
      eventData += dataContent;
    } else if (line.startsWith("event: ")) {
      // Extract event type if specified (for future use)
      // const eventType = line.slice(7);
    } else if (line === "data") {
      // Handle "data" without content (empty data)
      eventData = "";
    }
    // Ignore other SSE fields like id:, retry:, or comments starting with :
  }

  // Only return if we have data
  if (eventData) {
    // Handle special SSE signals
    if (eventData === "[DONE]") {
      console.log(`🏁 SSE Stream done signal received`);
      return null;
    }
    return eventData;
  }

  return null;
}

/**
 * Process SSE data with optional Zod validation
 */
function processSSEData<T>(
  eventData: string,
  controller: ReadableStreamDefaultController<MaybeZodObject<T>>,
  responseSchema: T | undefined,
  eventCount: number,
  url?: string
): void {
  try {
    const parsed = JSON.parse(eventData);

    console.log(`📨 SSE Event #${eventCount} for ${url || "stream"}:`, {
      dataPreview: JSON.stringify(parsed).substring(0, 200),
      hasSchema: !!responseSchema,
    });

    // Apply Zod validation if schema provided
    const validated = responseSchema
      ? (responseSchema as any).parse(parsed)
      : parsed;

    controller.enqueue(validated);
  } catch (parseError) {
    // Log but don't fail on individual parse errors
    console.error(`❌ SSE parse/validation error for ${url || "stream"}:`, {
      error: parseError,
      eventData,
      eventNumber: eventCount,
    });
  }
}

/**
 * Process remaining SSE buffer
 */
function processSSEBuffer<T>(
  buffer: string,
  controller: ReadableStreamDefaultController<MaybeZodObject<T>>,
  responseSchema: T | undefined,
  eventCount: number,
  url?: string
): void {
  const result = parseSSEEvent(buffer);
  if (result) {
    processSSEData(result, controller, responseSchema, eventCount + 1, url);
  }
}
