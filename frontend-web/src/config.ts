export interface AppConfig {
  apiBaseUrl: string;
  pollIntervalMs: number;
  pollTimeoutMs: number;
}

export const appConfig: AppConfig = {
  apiBaseUrl: (import.meta.env.VITE_API_BASE_URL || "").replace(/\/$/, ""),
  pollIntervalMs: Number(import.meta.env.VITE_POLL_INTERVAL_MS) || 2500,
  pollTimeoutMs: Number(import.meta.env.VITE_POLL_TIMEOUT_MS) || 90000,
};

export function isApiConfigured(): boolean {
  return Boolean(appConfig.apiBaseUrl);
}
