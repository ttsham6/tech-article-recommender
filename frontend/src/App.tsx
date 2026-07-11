import ProfileCard from "./components/ProfileCard";
import RecommendationForm from "./components/RecommendationForm";
import RecommendationResults from "./components/RecommendationResults";
import { isApiConfigured } from "./config";
import { useLiff } from "./hooks/useLiff";
import { useRecommendationJob } from "./hooks/useRecommendationJob";

export default function App() {
  const liffState = useLiff();
  const recommendation = useRecommendationJob(liffState.token);
  const canSubmit = isApiConfigured() && (liffState.phase === "ready" || liffState.phase === "unconfigured");
  const resultItems = recommendation.result?.items ?? [];
  const shouldShowResultMessage = recommendation.status !== "idle";

  return (
    <div className="app-shell">
      <header className="hero">
        <p className="eyebrow">LINE Mini App</p>
        <h1>Tech Article Recommender</h1>
        <p className="hero-copy">興味を書く。おすすめ記事3件 返す。</p>
        <ProfileCard profile={liffState.profile} />
      </header>

      <main className="content">
        <section className="panel">
          <div className="panel-head">
            <h2>記事リクエスト</h2>
            <span className={`status-chip ${liffState.statusClassName}`}>{liffState.statusText}</span>
          </div>

          <RecommendationForm
            disabled={!canSubmit || recommendation.isSubmitting}
            onSubmit={recommendation.submit}
          />

          {!liffState.isConfigured || !isApiConfigured() ? (
            <div className="config-note">
              {!liffState.isConfigured ? "VITE_LIFF_ID 設定必要。" : ""}
              {!liffState.isConfigured && !isApiConfigured() ? " " : ""}
              {!isApiConfigured() ? "VITE_API_BASE_URL 設定必要。" : ""}
            </div>
          ) : null}
        </section>

        <section className="panel">
          <div className="panel-head">
            <h2>おすすめ記事</h2>
            <span className={`status-chip ${resultItems.length > 0 ? "is-succeeded" : "is-idle"}`}>
              {resultItems.length > 0 ? `${resultItems.length}件` : "結果なし"}
            </span>
          </div>
          {shouldShowResultMessage ? <p className="message">{recommendation.message}</p> : null}
          <RecommendationResults result={recommendation.result} openWindow={liffState.openWindow} />
        </section>
      </main>
    </div>
  );
}
