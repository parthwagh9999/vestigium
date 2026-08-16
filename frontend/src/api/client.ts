import axios, { type InternalAxiosRequestConfig } from 'axios';
import { useAuthStore } from '@/stores/auth';
import { useConsoleStore } from '@/stores/consoleStore';

interface TimedAxiosRequestConfig extends InternalAxiosRequestConfig {
  _startTime?: number;
  _retry?: boolean;
}

const apiClient = axios.create({
  baseURL: '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
});

apiClient.interceptors.request.use((config: TimedAxiosRequestConfig) => {
  config._startTime = performance.now();
  const token = useAuthStore.getState().accessToken;
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

apiClient.interceptors.response.use(
  (response) => {
    const config = response.config as TimedAxiosRequestConfig;
    const duration = config._startTime ? Math.round(performance.now() - config._startTime) : 0;

    // Log API call
    useConsoleStore.getState().addApiLog({
      method: (config.method || 'GET').toUpperCase(),
      url: config.url || '',
      status: response.status,
      statusText: response.statusText || 'OK',
      durationMs: duration,
    });

    return response;
  },
  async (error) => {
    const originalRequest = error.config as TimedAxiosRequestConfig;
    const duration = originalRequest?._startTime ? Math.round(performance.now() - originalRequest._startTime) : 0;

    if (error.response) {
      useConsoleStore.getState().addApiLog({
        method: (originalRequest?.method || 'GET').toUpperCase(),
        url: originalRequest?.url || '',
        status: error.response.status,
        statusText: error.response.statusText || 'ERROR',
        durationMs: duration,
      });
    }

    if (error.response?.status === 401 && originalRequest && !originalRequest._retry) {
      originalRequest._retry = true;

      const refreshToken = useAuthStore.getState().refreshToken;
      if (refreshToken) {
        try {
          const { data } = await axios.post('/api/v1/auth/refresh', {
            refresh_token: refreshToken,
          });
          useAuthStore.getState().updateTokens(data.access_token, data.refresh_token);
          originalRequest.headers.Authorization = `Bearer ${data.access_token}`;
          return apiClient(originalRequest);
        } catch {
          useAuthStore.getState().logout();
          window.location.href = '/login';
        }
      } else {
        useAuthStore.getState().logout();
        window.location.href = '/login';
      }
    }

    return Promise.reject(error);
  },
);

export default apiClient;

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface IDResponse {
  id: string;
  message: string;
}
