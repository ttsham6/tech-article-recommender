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
        maxLength={200}
        rows={6}
        placeholder="例: Amazon Bedrock の最新機能を知りたい。導入や活用例が分かる記事を読みたい。"
        required
        value={preference}
        onChange={(event) => setPreference(event.target.value)}
      />
      <div className="field-meta">
        <span>最大 200 文字</span>
        <span>{preference.length} / 200</span>
      </div>
      <button className="primary-button" type="submit" disabled={disabled}>
        {disabled ? "取得中" : "おすすめ取得"}
      </button>
    </form>
  );
}
