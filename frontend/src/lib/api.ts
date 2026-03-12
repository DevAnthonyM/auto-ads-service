import axios from "axios";
import { useAuthStore } from "./auth";
import type { CarsQueryParams, LoginRequest, PaginatedCars, TokenResponse } from "@/types";

/** Axios instance configured for the backend API. */
const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
  headers: { "Content-Type": "application/json" },
});

// Attach JWT token to every request
api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().token;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Auto-logout on 401 responses
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      useAuthStore.getState().logout();
      if (typeof window !== "undefined") {
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  }
);

/** Authenticate and receive JWT token. */
export async function loginApi(data: LoginRequest): Promise<TokenResponse> {
  const response = await api.post<TokenResponse>("/api/login", data);
  return response.data;
}

/** Fetch paginated car listings with optional filters. */
export async function getCarsApi(params: CarsQueryParams = {}): Promise<PaginatedCars> {
  // Remove undefined/empty params
  const cleanParams = Object.fromEntries(
    Object.entries(params).filter(([, v]) => v !== undefined && v !== "" && v !== null)
  );
  const response = await api.get<PaginatedCars>("/api/cars", { params: cleanParams });
  return response.data;
}

export default api;