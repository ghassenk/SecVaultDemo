/// <reference types="vite/client" />

import type { 
  AuthTokens, 
  LoginCredentials, 
  RegisterCredentials, 
  User,
  Secret,
  SecretMetadata,
  SecretCreate,
  SecretUpdate,
  PaginatedResponse,
  ApiError
} from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

// Token storage in memory (NOT localStorage for security)
let accessToken: string | null = null;
let refreshToken: string | null = null;

// Token getters/setters for AuthContext to use
export const getAccessToken = () => accessToken;
export const getRefreshToken = () => refreshToken;

export const setTokens = (tokens: AuthTokens | null) => {
  if (tokens) {
    accessToken = tokens.access_token;
    refreshToken = tokens.refresh_token;
  } else {
    accessToken = null;
    refreshToken = null;
  }
};

// Check if we have tokens
export const hasTokens = () => !!accessToken;

// Fetch wrapper with auth and error handling
async function apiFetch<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...options.headers,
  };

  // Add auth header if we have a token
  if (accessToken) {
    (headers as Record<string, string>)['Authorization'] = `Bearer ${accessToken}`;
  }

  const response = await fetch(url, {
    ...options,
    headers,
  });

  // Handle 401 - try to refresh token
  if (response.status === 401 && refreshToken && !endpoint.includes('/auth/refresh')) {
    const refreshed = await tryRefreshToken();
    if (refreshed) {
      // Retry original request with new token
      (headers as Record<string, string>)['Authorization'] = `Bearer ${accessToken}`;
      const retryResponse = await fetch(url, { ...options, headers });
      if (!retryResponse.ok) {
        const error: ApiError = await retryResponse.json().catch(() => ({ detail: 'Request failed' }));
        throw new Error(error.detail);
      }
      return retryResponse.json();
    }
    // Refresh failed - clear tokens
    setTokens(null);
    throw new Error('Session expired. Please log in again.');
  }

  if (!response.ok) {
    const error: ApiError = await response.json().catch(() => ({ detail: 'Request failed' }));
    throw new Error(error.detail);
  }

  // Handle 204 No Content
  if (response.status === 204) {
    return undefined as T;
  }

  return response.json();
}

// Try to refresh the access token
async function tryRefreshToken(): Promise<boolean> {
  if (!refreshToken) return false;

  try {
    const response = await fetch(`${API_BASE_URL}/auth/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });

    if (!response.ok) {
      return false;
    }

    const tokens: AuthTokens = await response.json();
    setTokens(tokens);
    return true;
  } catch {
    return false;
  }
}

// Auth API
export const authApi = {
  register: (credentials: RegisterCredentials): Promise<User> =>
    apiFetch('/auth/register', {
      method: 'POST',
      body: JSON.stringify(credentials),
    }),

  login: async (credentials: LoginCredentials): Promise<AuthTokens> => {
    const tokens = await apiFetch<AuthTokens>('/auth/login', {
      method: 'POST',
      body: JSON.stringify(credentials),
    });
    setTokens(tokens);
    return tokens;
  },

  logout: async (): Promise<void> => {
    try {
      await apiFetch('/auth/logout', { method: 'POST' });
    } finally {
      setTokens(null);
    }
  },

  getMe: (): Promise<User> => apiFetch('/auth/me'),

  changePassword: (currentPassword: string, newPassword: string): Promise<{ message: string }> =>
    apiFetch('/auth/change-password', {
      method: 'POST',
      body: JSON.stringify({ current_password: currentPassword, new_password: newPassword }),
    }),
};

// Secrets API
export const secretsApi = {
  list: (page = 1, size = 10): Promise<PaginatedResponse<SecretMetadata>> =>
    apiFetch(`/secrets?page=${page}&size=${size}`),

  get: (id: string): Promise<Secret> => 
    apiFetch(`/secrets/${id}`),

  create: (data: SecretCreate): Promise<Secret> =>
    apiFetch('/secrets', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  update: (id: string, data: SecretUpdate): Promise<Secret> =>
    apiFetch(`/secrets/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }),

  delete: (id: string): Promise<void> =>
    apiFetch(`/secrets/${id}`, { method: 'DELETE' }),
};
