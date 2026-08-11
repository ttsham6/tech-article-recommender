import { useState, type FormEvent } from "react";

interface RecommendationFormProps {
  disabled: boolean;
  isSubmitting: boolean;
  onSubmit: (preference: string) => void | Promise<void>;
}

export default function RecommendationForm({
  disabled,
  isSubmitting,
  onSubmit,
}: RecommendationFormProps) {
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
        placeholder="例: Amazon Bedrock の最新機能を知りたい。導入やユースケースが分かる記事を読みたい。"
        required
        value={preference}
        onChange={(event) => setPreference(event.target.value)}
      />
      <div className="field-meta">
        <span>最大200文字です</span>
        <span>{preference.length} / 200</span>
      </div>
      <button className="primary-button" type="submit" disabled={disabled}>
        {isSubmitting ? "取得しています" : "おすすめを取得する"}
      </button>
    </form>
  );
}
