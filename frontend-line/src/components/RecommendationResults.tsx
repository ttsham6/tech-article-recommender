import type { RecommendationResult } from "../types";
import { getRecommendationUrlLabel, normalizeRecommendationUrl } from "../lib/recommendationUrl";

interface RecommendationResultsProps {
  result: RecommendationResult | null;
  openWindow: (url: string) => void;
}

export default function RecommendationResults({ result, openWindow }: RecommendationResultsProps) {
  const items = (result?.items ?? []).map((item, index) => ({
    ...item,
    key: `${item.title}-${item.url}-${index}`,
    normalizedUrl: normalizeRecommendationUrl(item.url),
  }));

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
        <li className="article-card" key={item.key}>
          <h3 className="article-title">{item.title}</h3>
          <p className="article-reason">{item.reason}</p>
          <div className="article-actions">
            <p className="job-id">
              {item.normalizedUrl ? getRecommendationUrlLabel(item.normalizedUrl) : "URL 無効"}
            </p>
            <button
              className="article-link"
              type="button"
              disabled={!item.normalizedUrl}
              onClick={() => item.normalizedUrl && openWindow(item.normalizedUrl)}
            >
              {item.normalizedUrl ? "記事開く" : "URL 修正必要"}
            </button>
          </div>
        </li>
      ))}
    </ul>
  );
}
