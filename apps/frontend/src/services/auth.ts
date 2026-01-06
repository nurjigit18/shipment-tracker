import { apiClient } from './api';

export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: {
    id: number;
    username: string;
    role: string;
    organization_id: number;
  };
}

export const authService = {
  async login(credentials: LoginRequest): Promise<LoginResponse> {
    return apiClient.post<LoginResponse>('/api/auth/login', credentials);
  },

  logout() {
    localStorage.removeItem('auth_token');
    localStorage.removeItem('ne_auth');
  },

  getStoredAuth() {
    const stored = localStorage.getItem('ne_auth');
    return stored ? JSON.parse(stored) : null;
  },

  storeAuth(token: string, user: LoginResponse['user']) {
    localStorage.setItem('auth_token', token);
    localStorage.setItem('ne_auth', JSON.stringify(user));
  }
};
