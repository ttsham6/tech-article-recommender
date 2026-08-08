import { useState, type FormEvent } from "react";

interface RecommendationFormProps {
  disabled: boolean;
  onSubmit: (preference: string) => void | Promise<void>;
}

export default function RecommendationForm({ disabled, onSubmit }: RecommendationFormProps) {
  const [preference, setPreference] = useState("");

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmed = preference.trim();
    if (!trimmed) {
      return;
    }
    void onSubmit(trimmed);
  }

  return (
    <form className="request-form" onSubmit={handleSubmit}>
      <label className="field-label" htmlFor="preference">
        知りたい技術
      </label>
      <textarea
        id="preference"
        name="preference"
        maxLength={500}
        rows={6}
        placeholder="例: Bedrock AgentCore の設計パターン。実装例 多め。"
        required
        value={preference}
        onChange={(event) => setPreference(event.target.value)}
      />
      <div className="field-meta">
        <span>最大 500 文字</span>
        <span>{preference.length} / 500</span>
      </div>
      <button className="primary-button" type="submit" disabled={disabled}>
        {disabled ? "取得中" : "おすすめ取得"}
      </button>
    </form>
  );
}
