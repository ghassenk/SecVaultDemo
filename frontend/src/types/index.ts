// User types
export interface User {
  id: string;
  email: string;
  is_active: boolean;
  created_at: string;
  last_login_at: string | null;
}

// Auth types
export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterCredentials {
  email: string;
  password: string;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

// Secret types
export interface SecretMetadata {
  id: string;
  name: string;
  created_at: string;
  updated_at: string;
}

export interface Secret extends SecretMetadata {
  content: string;
}

export interface SecretCreate {
  name: string;
  content: string;
}

export interface SecretUpdate {
  name?: string;
  content?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

// API error
export interface ApiError {
  detail: string;
}
