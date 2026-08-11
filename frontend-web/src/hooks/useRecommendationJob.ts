import { useEffect, useRef, useState, type MutableRefObject } from "react";

import { appConfig } from "../config";
import { createRecommendation, fetchRecommendationJob } from "../lib/api";
import type { RecommendationJobResponse, RecommendationJobStatus, RecommendationResult } from "../types";

export interface RecommendationViewState {
  jobId: string | null;
  status: RecommendationJobStatus | "idle";
  message: string;
  result: RecommendationResult | null;
}

export interface RecommendationController extends RecommendationViewState {
  isSubmitting: boolean;
  submit: (preference: string) => Promise<void>;
}

const initialViewState: RecommendationViewState = {
  jobId: null,
  status: "idle",
  message: "内容を入力して送信してください。",
  result: null,
};

export function useRecommendationJob(): RecommendationController {
  const [viewState, setViewState] = useState<RecommendationViewState>(initialViewState);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const timerRef = useRef<number | null>(null);
  const startedAtRef = useRef(0);

  useEffect(() => () => clearPolling(timerRef), []);

  async function submit(preference: string): Promise<void> {
    clearPolling(timerRef);
    setIsSubmitting(true);
    setViewState({
      jobId: null,
      status: "pending",
      message: "リクエストを作成しています。",
      result: null,
    });

    try {
      const accepted = await createRecommendation({ preference });
      startedAtRef.current = Date.now();
      setViewState({
        jobId: accepted.job_id,
        status: accepted.status,
        message: "記事の探索を開始しました。結果をお待ちください。",
        result: null,
      });
      void poll(accepted.job_id);
    } catch (error) {
      setIsSubmitting(false);
      setViewState({
        jobId: null,
        status: "failed",
        message: normalizeError(error),
        result: null,
      });
    }
  }

  async function poll(jobId: string): Promise<void> {
    try {
      const job = await fetchRecommendationJob({ jobId });

      if (job.status === "pending") {
        setPollingState(jobId, "pending", "記事探索の開始を待っています。");
        scheduleNext(jobId);
        return;
      }

      if (job.status === "running") {
        setPollingState(jobId, "running", "記事を探索しています。");
        scheduleNext(jobId);
        return;
      }

      if (job.status === "failed") {
        clearPolling(timerRef);
        setIsSubmitting(false);
        setViewState({
          jobId,
          status: "failed",
          message: job.error_message || "処理に失敗しました。",
          result: null,
        });
        return;
      }

      finishSucceeded(jobId, job);
    } catch (error) {
      clearPolling(timerRef);
      setIsSubmitting(false);
      setViewState({
        jobId,
        status: "failed",
        message: normalizeError(error),
        result: null,
      });
    }
  }

  function setPollingState(jobId: string, status: RecommendationJobStatus, message: string): void {
    setViewState({
      jobId,
      status,
      message,
      result: null,
    });
  }

  function finishSucceeded(jobId: string, job: RecommendationJobResponse): void {
    clearPolling(timerRef);
    setIsSubmitting(false);
    const itemCount = job.result?.items.length ?? 0;
    setViewState({
      jobId,
      status: "succeeded",
      message:
        job.result?.message ||
        (itemCount > 0 ? `おすすめ記事を${itemCount}件取得しました。` : "一致する記事は見つかりませんでした。"),
      result: job.result,
    });
  }

  function scheduleNext(jobId: string): void {
    if (Date.now() - startedAtRef.current > appConfig.pollTimeoutMs) {
      clearPolling(timerRef);
      setIsSubmitting(false);
      setViewState({
        jobId,
        status: "failed",
        message: "時間をおいて、もう一度お試しください。",
        result: null,
      });
      return;
    }

    timerRef.current = window.setTimeout(() => {
      void poll(jobId);
    }, appConfig.pollIntervalMs);
  }

  return {
    ...viewState,
    isSubmitting,
    submit,
  };
}

function clearPolling(timerRef: MutableRefObject<number | null>): void {
  if (timerRef.current !== null) {
    window.clearTimeout(timerRef.current);
    timerRef.current = null;
  }
}

function normalizeError(error: unknown): string {
  if (error instanceof Error) {
    return error.message;
  }
  return "不明なエラーが発生しました。";
}
