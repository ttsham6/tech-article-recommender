import { appConfig } from "../config";
import type { RecommendationAcceptedResponse, RecommendationJobResponse } from "../types";

export async function createRecommendation(params: {
  preference: string;
  token: string | null;
}): Promise<RecommendationAcceptedResponse> {
  const response = await fetch(buildUrl("/recommendations"), {
    method: "POST",
    headers: buildHeaders(params.token),
    body: JSON.stringify({ preference: params.preference }),
  });
  return parseJsonResponse<RecommendationAcceptedResponse>(response);
}

export async function fetchRecommendationJob(params: {
  jobId: string;
  token: string | null;
}): Promise<RecommendationJobResponse> {
  const response = await fetch(buildUrl(`/recommendations/${params.jobId}`), {
    method: "GET",
    headers: buildHeaders(params.token),
  });
  return parseJsonResponse<RecommendationJobResponse>(response);
}

function buildUrl(pathname: string): string {
  if (!appConfig.apiBaseUrl) {
    throw new Error("VITE_API_BASE_URL 未設定");
  }
  return `${appConfig.apiBaseUrl}${pathname}`;
}

function buildHeaders(token: string | null): HeadersInit {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  return headers;
}

async function parseJsonResponse<T>(response: Response): Promise<T> {
  const text = await response.text();
  const body: unknown = text ? JSON.parse(text) : null;

  if (!response.ok) {
    const detail = getErrorDetail(body);
    throw new Error(detail ?? `API error: ${response.status}`);
  }

  return body as T;
}

function getErrorDetail(body: unknown): string | null {
  if (typeof body === "object" && body !== null && "detail" in body) {
    const detail = body.detail;
    if (typeof detail === "string") {
      return detail;
    }
  }
  return null;
}
