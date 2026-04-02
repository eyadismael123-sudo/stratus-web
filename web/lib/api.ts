import axios, { AxiosError, type AxiosRequestConfig } from "axios";
import { createClient } from "./supabase";

const BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

/** Axios instance pointing at FastAPI backend */
export const api = axios.create({
  baseURL: BASE_URL,
  headers: { "Content-Type": "application/json" },
  timeout: 15_000,
});

// Attach Supabase JWT to every request
api.interceptors.request.use(async (config) => {
  const supabase = createClient();
  const {
    data: { session },
  } = await supabase.auth.getSession();

  if (session?.access_token) {
    config.headers.Authorization = `Bearer ${session.access_token}`;
  }
  return config;
});

// Normalise error responses
api.interceptors.response.use(
  (response) => response,
  (error: AxiosError<{ error_message?: string }>) => {
    const message =
      error.response?.data?.error_message ??
      error.message ??
      "An unexpected error occurred";
    return Promise.reject(new Error(message));
  }
);

/** Typed GET helper */
export async function get<T>(
  path: string,
  config?: AxiosRequestConfig
): Promise<T> {
  const response = await api.get<{ success: boolean; data: T }>(path, config);
  return response.data.data;
}

/** Typed POST helper */
export async function post<T>(
  path: string,
  body?: unknown,
  config?: AxiosRequestConfig
): Promise<T> {
  const response = await api.post<{ success: boolean; data: T }>(
    path,
    body,
    config
  );
  return response.data.data;
}

/** Typed PATCH helper */
export async function patch<T>(
  path: string,
  body?: unknown,
  config?: AxiosRequestConfig
): Promise<T> {
  const response = await api.patch<{ success: boolean; data: T }>(
    path,
    body,
    config
  );
  return response.data.data;
}

/** Typed DELETE helper */
export async function del<T>(
  path: string,
  config?: AxiosRequestConfig
): Promise<T> {
  const response = await api.delete<{ success: boolean; data: T }>(
    path,
    config
  );
  return response.data.data;
}
