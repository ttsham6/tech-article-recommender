const MARKDOWN_LINK_PATTERN = /\[[^\]]*?\]\((https?:\/\/[^)\s]+)\)/i;

export function normalizeRecommendationUrl(rawUrl: string): string | null {
  const trimmed = rawUrl.trim();
  if (!trimmed) {
    return null;
  }

  const markdownMatch = trimmed.match(MARKDOWN_LINK_PATTERN);
  const extractedUrl = markdownMatch?.[1] ?? trimmed;
  const strippedUrl = stripWrappingCharacters(extractedUrl).replace(/[.,;!?]+$/, "");
  const withScheme = /^[a-z][a-z\d+\-.]*:\/\//i.test(strippedUrl) ? strippedUrl : `https://${strippedUrl}`;

  try {
    const parsed = new URL(withScheme);
    if (!["http:", "https:"].includes(parsed.protocol) || !parsed.hostname.includes(".")) {
      return null;
    }
    return parsed.toString();
  } catch {
    return null;
  }
}

export function getRecommendationUrlLabel(url: string): string {
  try {
    const parsed = new URL(url);
    return parsed.hostname;
  } catch {
    return url;
  }
}

function stripWrappingCharacters(value: string): string {
  return value.replace(/^[\s<("'[]+/, "").replace(/[\s>")'\]]+$/, "");
}
