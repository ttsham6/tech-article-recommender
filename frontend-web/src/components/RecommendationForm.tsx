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
      <p className="field-note">※現在、入力は英語のみ対応しています。</p>
      <textarea
        id="preference"
        name="preference"
        maxLength={500}
        rows={6}
        placeholder="Example: I want to learn Bedrock AgentCore design patterns with plenty of implementation examples."
        required
        value={preference}
        onChange={(event) => setPreference(event.target.value)}
      />
      <div className="field-meta">
        <span>最大500文字です</span>
        <span>{preference.length} / 500</span>
      </div>
      <button className="primary-button" type="submit" disabled={disabled}>
        {isSubmitting ? "取得しています" : "おすすめを取得する"}
      </button>
    </form>
  );
}
