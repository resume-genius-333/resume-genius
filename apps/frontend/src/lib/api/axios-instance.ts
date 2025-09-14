import axios, {
  AxiosRequestConfig,
  AxiosError,
  InternalAxiosRequestConfig,
} from "axios";

// Use relative URL to go through Next.js proxy
const API_BASE_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "/api/proxy";

// Create axios instance with default config
const axiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// Queue to hold requests while refreshing token
let isRefreshing = false;
let failedQueue: Array<{
  resolve: (value: unknown) => void;
  reject: (error: unknown) => void;
}> = [];

const processQueue = (error: unknown, token: string | null = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });
  failedQueue = [];
};

// Request interceptor for auth token
axiosInstance.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    // Token is set in AuthContext when logging in or refreshing
    const token = localStorage.getItem("access_token");
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling and token refresh
axiosInstance.interceptors.response.use(
  (response) => {
    return response;
  },
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & {
      _retry?: boolean;
    };

    // Handle 401 errors (unauthorized)
    if (
      error.response?.status === 401 &&
      originalRequest &&
      !originalRequest._retry
    ) {
      if (isRefreshing) {
        // If already refreshing, queue this request
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        })
          .then((token) => {
            if (originalRequest.headers) {
              originalRequest.headers.Authorization = `Bearer ${token}`;
            }
            return axiosInstance(originalRequest);
          })
          .catch((err) => {
            return Promise.reject(err);
          });
      }

      originalRequest._retry = true;
      isRefreshing = true;

      const refreshToken = localStorage.getItem("refresh_token");

      if (!refreshToken) {
        // No refresh token, redirect to login
        processQueue(error, null);
        isRefreshing = false;
        if (typeof window !== "undefined") {
          window.location.href = "/auth/sign-in";
        }
        return Promise.reject(error);
      }

      try {
        // Import here to avoid circular dependency
        const { refreshTokenApiV1AuthRefreshPost } = await import(
          "./generated/api"
        );
        const data = await refreshTokenApiV1AuthRefreshPost({
          refresh_token: refreshToken,
        });

        const { access_token, expires_in } = data;

        // Save new tokens (refresh token stays the same)
        localStorage.setItem("access_token", access_token);
        // Keep the existing refresh token
        const expiryTime = new Date().getTime() + expires_in * 1000;
        localStorage.setItem("token_expiry", expiryTime.toString());

        axiosInstance.defaults.headers.common["Authorization"] =
          `Bearer ${access_token}`;
        processQueue(null, access_token);

        if (originalRequest.headers) {
          originalRequest.headers.Authorization = `Bearer ${access_token}`;
        }
        return axiosInstance(originalRequest);
      } catch (refreshError) {
        processQueue(refreshError, null);
        // Clear tokens and redirect to login
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
        localStorage.removeItem("token_expiry");
        delete axiosInstance.defaults.headers.common["Authorization"];

        if (typeof window !== "undefined") {
          window.location.href = "/auth/sign-in";
        }
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  }
);

// Custom error class for API errors
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

/**
 * Custom axios instance for Orval
 * This function is used by Orval to make API requests
 */
export const customAxiosInstance = <T>(
  config: AxiosRequestConfig
): Promise<T> => {
  const source = axios.CancelToken.source();

  const promise = axiosInstance({
    ...config,
    cancelToken: source.token,
  }).then(({ data }) => data);

  return promise;
};

// Export the axios instance for direct use if needed
export default axiosInstance;
