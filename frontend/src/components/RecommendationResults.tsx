import type { RecommendationResult } from "../types";

interface RecommendationResultsProps {
  result: RecommendationResult | null;
  openWindow: (url: string) => void;
}

export default function RecommendationResults({ result, openWindow }: RecommendationResultsProps) {
  const items = result?.items ?? [];

  if (items.length === 0) {
    return (
      <div className="empty-state">
        <p>まだ結果なし。</p>
      </div>
    );
  }

  return (
    <ul className="result-list">
      {items.map((item) => (
        <li className="article-card" key={item.url}>
          <h3 className="article-title">{item.title}</h3>
          <p className="article-reason">{item.reason}</p>
          <div className="article-actions">
            <p className="job-id">{item.url}</p>
            <button className="article-link" type="button" onClick={() => openWindow(item.url)}>
              記事開く
            </button>
          </div>
        </li>
      ))}
    </ul>
  );
}
