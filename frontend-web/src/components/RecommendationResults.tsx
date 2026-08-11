import { normalizeRecommendationUrl } from "../lib/recommendationUrl";
import type { RecommendationResult } from "../types";

interface RecommendationResultsProps {
  result: RecommendationResult | null;
}

export default function RecommendationResults({ result }: RecommendationResultsProps) {
  const items = (result?.items ?? []).map((item, index) => ({
    ...item,
    key: `${item.title}-${item.url}-${index}`,
    normalizedUrl: normalizeRecommendationUrl(item.url),
  }));

  if (items.length === 0) {
    return (
      <div className="empty-state">
        <p>{result?.message ?? "まだ結果はありません。"}</p>
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
            <button
              className="article-link"
              type="button"
              disabled={!item.normalizedUrl}
              onClick={() => item.normalizedUrl && window.open(item.normalizedUrl, "_blank", "noopener,noreferrer")}
            >
              {item.normalizedUrl ? "記事を開く" : "記事を開けません"}
            </button>
          </div>
        </li>
      ))}
    </ul>
  );
}
