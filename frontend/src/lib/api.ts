import type {
  Candle,
  DashboardSummary,
  Contract,
} from '@/types';

const API_BASE = (import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000').replace(/\/$/, '');
const API_ROOT = `${API_BASE}/api`;

async function parseError(response: Response): Promise<Error> {
  try {
    const body = await response.json();
    if (body?.detail) {
      return new Error(typeof body.detail === 'string' ? body.detail : JSON.stringify(body.detail));
    }
    if (body?.message) {
      return new Error(body.message);
    }
    return new Error(response.statusText || 'Request failed');
  } catch {
    return new Error(response.statusText || 'Request failed');
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_ROOT}${path}`, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...(init?.headers ?? {}),
    },
  });

  if (!response.ok) {
    throw await parseError(response);
  }

  return (await response.json()) as T;
}

export async function fetchDashboard(
  symbol: string,
  timeframe: string,
): Promise<DashboardSummary> {
  return await request<DashboardSummary>(`/dashboard?symbol=${encodeURIComponent(symbol)}&timeframe=${encodeURIComponent(timeframe)}`);
}

export interface CandlesResponse {
  symbol: string;
  timeframe: string;
  candles: Candle[];
  contract?: Contract;
}

export async function fetchCandles(
  symbol: string,
  timeframe: string,
  limit = 500,
): Promise<CandlesResponse> {
  return await request<CandlesResponse>(
    `/candles?symbol=${encodeURIComponent(symbol)}&timeframe=${encodeURIComponent(timeframe)}&limit=${limit}`,
  );
}

export async function searchContracts(query: string): Promise<Contract[]> {
  if (!query.trim()) {
    return [];
  }
  const result = await request<{ contracts: Contract[] }>(`/contracts?query=${encodeURIComponent(query)}`);
  return result.contracts ?? [];
}

export { API_ROOT };
