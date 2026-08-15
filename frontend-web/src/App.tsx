import RecommendationForm from "./components/RecommendationForm";
import RecommendationResults from "./components/RecommendationResults";
import { isApiConfigured } from "./config";
import { useRecommendationJob } from "./hooks/useRecommendationJob";

export default function App() {
  const recommendation = useRecommendationJob();
  const resultItems = recommendation.result?.items ?? [];
  const shouldShowResultMessage =
    recommendation.status !== "idle" && (recommendation.result === null || resultItems.length > 0);

  return (
    <div className="app-shell">
      <header className="hero">
        <h1>Tech Article Recommender</h1>
        <p className="hero-copy">
          興味のある技術領域を入力すると、AWSの記事をご案内します。
        </p>
      </header>

      <main className="content">
        <section className="panel">
          <div className="panel-head">
            <h2>記事リクエスト</h2>
            <span className={`status-chip ${statusClassName(recommendation.status)}`}>
              {statusText(recommendation.status)}
            </span>
          </div>

          <RecommendationForm
            disabled={!isApiConfigured() || recommendation.isSubmitting}
            isSubmitting={recommendation.isSubmitting}
            onSubmit={recommendation.submit}
          />
        </section>

        <section className="panel">
          <div className="panel-head">
            <h2>おすすめ記事</h2>
            <span className={`status-chip ${resultItems.length > 0 ? "is-succeeded" : "is-idle"}`}>
              {resultItems.length > 0 ? `${resultItems.length}件` : "結果はありません"}
            </span>
          </div>
          {shouldShowResultMessage ? <p className="message">{recommendation.message}</p> : null}
          <RecommendationResults result={recommendation.result} />
        </section>
      </main>
    </div>
  );
}

function statusText(status: "idle" | "pending" | "running" | "succeeded" | "failed"): string {
  switch (status) {
    case "pending":
      return "受付中です";
    case "running":
      return "探索中です";
    case "succeeded":
      return "完了しました";
    case "failed":
      return "エラーです";
    default:
      return "待機中です";
  }
}

function statusClassName(status: "idle" | "pending" | "running" | "succeeded" | "failed"): string {
  switch (status) {
    case "pending":
      return "is-pending";
    case "running":
      return "is-running";
    case "succeeded":
      return "is-succeeded";
    case "failed":
      return "is-failed";
    default:
      return "is-idle";
  }
}
