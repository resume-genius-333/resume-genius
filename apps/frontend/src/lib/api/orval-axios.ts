import axios, {
  AxiosRequestConfig,
  ResponseType,
  CancelTokenSource,
} from "axios";
import { Readable } from "stream";
import z, { ZodObject } from "zod";

// Use relative URL to go through Next.js proxy
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "/api/proxy";

// Create axios instance with default config
const axiosInstance = axios.create({
  baseURL: API_BASE_URL,
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
 * - if `responseType` is `stream`, then, we want the return type of this function
 *   to be `ReadableStream<T>`
 */
export async function customAxiosInstance<T = any, D = any>(
  config: CustomAxiosRequestConfig<D> & {
    responseSchema?: T;
  }
): Promise<MaybeZodObject<T> | ReadableStream<MaybeZodObject<T>>> {
  const source = axios.CancelToken.source();

  const isSseStreaming = config.responseType === "sse-stream";

  const headers: AxiosRequestConfig["headers"] = {
    ...config.headers,
  };

  if (isSseStreaming) {
    headers["Accept"] = "text/event-stream";
    headers["Cache-Control"] = "no-cache";
  }

  const params: AxiosRequestConfig<D> = {
    ...config,
    headers,
    responseType:
      config.responseType === "sse-stream" ? "stream" : config.responseType,
    // Add timestamp for duration calculation
    ...({
      requestStartTime: Date.now(),
    } as any),
  };

  // Log custom axios instance request
  console.log(
    `🔧 Custom Axios Instance: ${config.method || "GET"} ${config.url}`,
    {
      isSSE: isSseStreaming,
      responseType: config.responseType,
      hasSchema: !!config.responseSchema,
    }
  );

  const response = await axiosInstance(params);

  // Handle streaming response (SSE)
  if (isSseStreaming) {
    const data: Readable = response.data;
    console.log("📡 Starting SSE stream processing for:", config.url);
    return convertSSEStreamToReadableStream(
      data,
      config.responseSchema,
      source,
      config.url
    );
  }

  // Handle non-streaming response
  const responseData = response.data;

  // Apply Zod validation if schema provided
  if (config.responseSchema) {
    return (config.responseSchema as any).parse(responseData);
  }

  return responseData;
}

/**
 * Converts a Node.js Readable stream (SSE format) to a Web Streams API ReadableStream
 * with optional Zod validation
 */
function convertSSEStreamToReadableStream<T = any>(
  data: Readable,
  responseSchema?: T,
  cancelSource?: CancelTokenSource,
  url?: string
): ReadableStream<MaybeZodObject<T>> {
  return new ReadableStream<MaybeZodObject<T>>({
    async start(controller) {
      let buffer = "";
      let eventCount = 0;
      const streamStartTime = Date.now();

      console.log(`🌊 SSE Stream initialized for: ${url || "unknown"}`);

      data.on("data", (chunk: Buffer) => {
        try {
          buffer += chunk.toString();
          console.log(
            `📦 SSE Chunk received for ${url || "stream"}:`,
            `Size: ${chunk.length} bytes`,
            `Buffer size: ${buffer.length}`
          );

          // SSE events are separated by double newlines
          const events = buffer.split("\n\n");
          // Keep the last (potentially incomplete) event in the buffer
          buffer = events.pop() || "";

          for (const event of events) {
            if (!event.trim()) continue;

            // Parse SSE event
            const lines = event.split("\n");
            let eventData = "";
            let eventType = "message";

            for (const line of lines) {
              if (line.startsWith("data: ")) {
                // Extract data after "data: " prefix
                const dataContent = line.slice(6);
                eventData += dataContent;
              } else if (line.startsWith("event: ")) {
                // Extract event type if specified
                eventType = line.slice(7);
              } else if (line === "data") {
                // Handle "data" without content (empty data)
                eventData = "";
              }
              // Ignore other SSE fields like id:, retry:, or comments starting with :
            }

            // Only process if we have data
            if (eventData) {
              try {
                // Handle special SSE signals
                if (eventData === "[DONE]") {
                  // Common pattern for completion in SSE streams (e.g., OpenAI)
                  console.log(`🏁 SSE Stream done signal received for: ${url}`);
                  continue;
                }

                const parsed = JSON.parse(eventData);
                eventCount++;

                console.log(
                  `📨 SSE Event #${eventCount} for ${url || "stream"}:`,
                  {
                    eventType,
                    dataPreview: JSON.stringify(parsed).substring(0, 200),
                    hasSchema: !!responseSchema,
                  }
                );

                // Apply Zod validation if schema provided
                const validated = responseSchema
                  ? (responseSchema as any).parse(parsed)
                  : parsed;

                controller.enqueue(validated);
              } catch (parseError) {
                // Log but don't fail on individual parse errors
                console.error(
                  `❌ SSE parse/validation error for ${url || "stream"}:`,
                  {
                    error: parseError,
                    eventData,
                    eventType,
                    eventNumber: eventCount + 1,
                  }
                );
              }
            }
          }
        } catch (error) {
          controller.error(error);
        }
      });

      data.on("end", () => {
        const duration = Date.now() - streamStartTime;
        console.log(`✅ SSE Stream completed for ${url || "stream"}:`, {
          totalEvents: eventCount,
          duration: `${duration}ms`,
          remainingBuffer: buffer.length,
        });

        // Process any remaining buffer (last event without double newline)
        if (buffer.trim()) {
          const lines = buffer.split("\n");
          let eventData = "";

          for (const line of lines) {
            if (line.startsWith("data: ")) {
              eventData += line.slice(6);
            }
          }

          if (eventData && eventData !== "[DONE]") {
            try {
              const parsed = JSON.parse(eventData);
              const validated = responseSchema
                ? (responseSchema as any).parse(parsed)
                : parsed;
              controller.enqueue(validated);
            } catch (error) {
              console.error(
                `❌ Final SSE parse/validation error for ${url || "stream"}:`,
                error,
                { eventData }
              );
            }
          }
        }
        controller.close();
      });

      data.on("error", (error) => {
        console.error(`❌ SSE Stream error for ${url || "stream"}:`, error, {
          eventsProcessed: eventCount,
          duration: `${Date.now() - streamStartTime}ms`,
        });
        controller.error(error);
      });
    },
    cancel() {
      console.log(`🛑 SSE Stream cancelled for ${url || "stream"}`);
      // Cancel the axios request if the stream is cancelled
      cancelSource?.cancel("Stream cancelled");
      data.destroy();
    },
  });
}
