export interface RecommendationItem {
  title: string;
  url: string;
  reason: string;
}

export interface RecommendationResult {
  items: RecommendationItem[];
}

export type RecommendationJobStatus = "pending" | "running" | "succeeded" | "failed";

export interface RecommendationAcceptedResponse {
  job_id: string;
  status: "pending";
}

export interface RecommendationJobResponse {
  job_id: string;
  status: RecommendationJobStatus;
  result: RecommendationResult | null;
  error_message: string | null;
}
