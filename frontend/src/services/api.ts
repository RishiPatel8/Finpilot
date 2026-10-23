const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api/v1';

export class ApiError extends Error {
  status: number;
  data: any;

  constructor(message: string, status: number, data?: any) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.data = data;
  }
}

export const getAuthToken = (): string | null => {
  return localStorage.getItem('finpilot_token');
};

export const setAuthToken = (token: string): void => {
  localStorage.setItem('finpilot_token', token);
};

export const clearAuthToken = (): void => {
  localStorage.removeItem('finpilot_token');
};

export async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const token = getAuthToken();
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string>),
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const url = endpoint.startsWith('http') ? endpoint : `${API_BASE}${endpoint}`;

  try {
    const res = await fetch(url, {
      ...options,
      headers,
    });

    if (!res.ok) {
      let errorBody = {};
      try {
        errorBody = await res.json();
      } catch {
        errorBody = { message: res.statusText };
      }
      throw new ApiError(
        (errorBody as any).detail || 'API request failed',
        res.status,
        errorBody
      );
    }

    return await res.json();
  } catch (err) {
    if (err instanceof ApiError) {
      throw err;
    }
    throw new ApiError((err as Error).message || 'Network error', 0);
  }
}

export const checkHealth = async () => {
  return apiRequest<{
    status: string;
    app_name: string;
    environment: string;
    database: string;
    version: string;
  }>('/health');
};
