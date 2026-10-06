// lib/api/cryptoNews.ts
// CryptoCompare free News & Social API client — no API key required for public endpoints.

export interface NewsItem {
  id: string;
  title: string;
  body: string;
  url: string;
  source: string;
  publishedAt: number;   // unix timestamp (seconds)
  categories: string;
  imageUrl: string;
}

export interface CoinSentiment {
  score: number;       // 0–100
  positive: number;    // positive mentions
  negative: number;    // negative mentions
}

// Known CryptoCompare coin IDs for quick lookup
const SYMBOL_TO_COIN_ID: Record<string, number> = {
  BTC: 1182,
  ETH: 7605,
  SOL: 5426,
  BNB: 4943,
  XRP: 5031,
  DOGE: 4432,
  ADA: 321992,
};

/**
 * Fetch the latest crypto news articles (English, sorted by latest).
 * Endpoint: GET https://min-api.cryptocompare.com/data/v2/news/?lang=EN&sortOrder=latest
 */
export async function fetchCryptoNews(): Promise<NewsItem[]> {
  const res = await fetch(
    'https://min-api.cryptocompare.com/data/v2/news/?lang=EN&sortOrder=latest',
    { next: { revalidate: 120 } }
  );
  if (!res.ok) throw new Error(`CryptoCompare news error: ${res.status}`);

  const json = await res.json();
  const articles: any[] = json.Data ?? [];

  return articles.slice(0, 10).map((item: any) => ({
    id: String(item.id),
    title: item.title ?? '',
    body: item.body ?? '',
    url: item.url ?? '',
    source: item.source_info?.name ?? item.source ?? 'Unknown',
    publishedAt: item.published_on ?? 0,
    categories: item.categories ?? '',
    imageUrl: item.imageurl ?? '',
  }));
}

/**
 * Fetch social/sentiment data for a given symbol (e.g. "BTC", "ETH").
 * Endpoint: GET https://min-api.cryptocompare.com/data/social/coin/latest?coinId=<id>
 */
export async function fetchCoinSentiment(symbol: string): Promise<CoinSentiment> {
  const upperSymbol = symbol.toUpperCase().replace('USDT', '');
  const coinId = SYMBOL_TO_COIN_ID[upperSymbol];

  if (!coinId) {
    return { score: 50, positive: 0, negative: 0 };
  }

  const res = await fetch(
    `https://min-api.cryptocompare.com/data/social/coin/latest?coinId=${coinId}`,
    { next: { revalidate: 300 } }
  );
  if (!res.ok) throw new Error(`CryptoCompare sentiment error: ${res.status}`);

  const json = await res.json();
  const reddit = json.Data?.Reddit ?? {};
  const twitter = json.Data?.Twitter ?? {};

  const positive = (reddit.comments_per_day ?? 0) + (twitter.followers ?? 0) / 1000;
  const negative = reddit.active_users ?? 0;
  const total = positive + negative || 1;
  const score = Math.round((positive / total) * 100);

  return {
    score,
    positive: Math.round(positive),
    negative: Math.round(negative),
  };
}
