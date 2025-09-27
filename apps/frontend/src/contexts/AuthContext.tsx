"use client";

import React, {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
  ReactNode,
} from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import {
  loginApiV1AuthLoginPost,
  registerApiV1AuthRegisterPost,
  logoutApiV1AuthLogoutPost,
  getMeApiV1AuthMeGet,
  refreshTokenApiV1AuthRefreshPost,
} from "@/lib/api/generated/api";
import type {
  UserLoginRequest,
  UserRegisterRequest,
  UserResponse,
} from "@/lib/api/generated/schemas";
import axiosInstance from "@/lib/api/axios-instance";

interface AuthContextType {
  user: UserResponse | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (credentials: UserLoginRequest) => Promise<void>;
  register: (userData: UserRegisterRequest) => Promise<void>;
  logout: () => Promise<void>;
  refreshSession: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const TOKEN_KEY = "access_token";
const REFRESH_TOKEN_KEY = "refresh_token";
const TOKEN_EXPIRY_KEY = "token_expiry";

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const router = useRouter();

  // Load tokens from localStorage
  const loadTokens = useCallback(() => {
    if (typeof window === "undefined") return null;
    
    const token = localStorage.getItem(TOKEN_KEY);
    const refreshToken = localStorage.getItem(REFRESH_TOKEN_KEY);
    const expiry = localStorage.getItem(TOKEN_EXPIRY_KEY);
    
    if (!token || !refreshToken) return null;
    
    // Check if token is expired
    if (expiry && new Date().getTime() > parseInt(expiry)) {
      return { refreshToken, expired: true };
    }
    
    return { token, refreshToken, expired: false };
  }, []);

  // Save tokens to localStorage
  const saveTokens = useCallback(
    (accessToken: string, refreshToken: string, expiresIn: number) => {
      localStorage.setItem(TOKEN_KEY, accessToken);
      localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
      const expiryTime = new Date().getTime() + expiresIn * 1000;
      localStorage.setItem(TOKEN_EXPIRY_KEY, expiryTime.toString());
      
      // Update axios default header
      axiosInstance.defaults.headers.common["Authorization"] = `Bearer ${accessToken}`;
    },
    []
  );

  // Clear tokens from localStorage
  const clearTokens = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
    localStorage.removeItem(TOKEN_EXPIRY_KEY);
    delete axiosInstance.defaults.headers.common["Authorization"];
  }, []);

  // Fetch current user
  const fetchUser = useCallback(async () => {
    try {
      const data = await getMeApiV1AuthMeGet();
      setUser(data);
      setIsAuthenticated(true);
      return data;
    } catch (error) {
      console.error("Failed to fetch user:", error);
      setIsAuthenticated(false);
      throw error;
    }
  }, []);

  // Login function
  const login = useCallback(
    async (credentials: UserLoginRequest) => {
      try {
        const data = await loginApiV1AuthLoginPost(credentials);
        const { access_token, refresh_token, expires_in } = data;
        
        saveTokens(access_token, refresh_token, expires_in);
        await fetchUser();
        
        toast.success("Successfully logged in!");
        router.push("/dashboard");
      } catch (error) {
        const message =
          (error as { response?: { data?: { detail?: string } } })?.response?.data?.detail || "Login failed";
        toast.error(message);
        throw error;
      }
    },
    [saveTokens, fetchUser, router]
  );

  // Register function
  const register = useCallback(
    async (userData: UserRegisterRequest) => {
      try {
        await registerApiV1AuthRegisterPost(userData);
        toast.success("Registration successful! Please log in.");
        router.push("/auth/sign-in");
      } catch (error) {
        const message =
          (error as { response?: { data?: { detail?: string } } })?.response?.data?.detail || "Registration failed";
        toast.error(message);
        throw error;
      }
    },
    [router]
  );

  // Logout function
  const logout = useCallback(async () => {
    try {
      await logoutApiV1AuthLogoutPost();
    } catch (error) {
      console.error("Logout API error:", error);
    } finally {
      clearTokens();
      setUser(null);
      setIsAuthenticated(false);
      router.push("/auth/sign-in");
      toast.success("Successfully logged out");
    }
  }, [clearTokens, router]);

  // Refresh session
  const refreshSession = useCallback(async () => {
    const tokens = loadTokens();
    if (!tokens?.refreshToken) {
      throw new Error("No refresh token available");
    }

    try {
      const data = await refreshTokenApiV1AuthRefreshPost({
        refresh_token: tokens.refreshToken,
      });
      
      const { access_token, expires_in } = data;
      // Keep the existing refresh token since the API doesn't return a new one
      saveTokens(access_token, tokens.refreshToken, expires_in);
      
      await fetchUser();
    } catch (error) {
      console.error("Failed to refresh session:", error);
      clearTokens();
      setUser(null);
      setIsAuthenticated(false);
      throw error;
    }
  }, [loadTokens, saveTokens, fetchUser, clearTokens]);

  // Initialize auth state on mount
  useEffect(() => {
    const initAuth = async () => {
      setIsLoading(true);
      const tokens = loadTokens();
      
      if (!tokens) {
        setIsLoading(false);
        return;
      }

      try {
        if (tokens.expired && tokens.refreshToken) {
          // Token expired, try to refresh
          await refreshSession();
        } else if (tokens.token) {
          // Token exists and not expired, set it and fetch user
          axiosInstance.defaults.headers.common["Authorization"] = `Bearer ${tokens.token}`;
          await fetchUser();
        }
      } catch (error) {
        console.error("Auth initialization failed:", error);
        clearTokens();
      } finally {
        setIsLoading(false);
      }
    };

    initAuth();
  }, [clearTokens, fetchUser, loadTokens, refreshSession]);

  // Set up auto-refresh before token expires
  useEffect(() => {
    if (!isAuthenticated) return;

    const expiryStr = localStorage.getItem(TOKEN_EXPIRY_KEY);
    if (!expiryStr) return;

    const expiry = parseInt(expiryStr);
    const now = new Date().getTime();
    const timeUntilExpiry = expiry - now;

    // Refresh 1 minute before expiry
    const refreshTime = timeUntilExpiry - 60000;
    
    if (refreshTime > 0) {
      const timer = setTimeout(() => {
        refreshSession().catch(console.error);
      }, refreshTime);

      return () => clearTimeout(timer);
    }
  }, [isAuthenticated, refreshSession]);

  const value = {
    user,
    isLoading,
    isAuthenticated,
    login,
    register,
    logout,
    refreshSession,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}